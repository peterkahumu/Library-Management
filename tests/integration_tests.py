from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from accounts.models import UserRoles
from books.models import Book, Genre
from book_circulation.models import Transaction

User = get_user_model()


class BorrowingWorkflowTests(TestCase):
    """End-to-end tests for the borrowing lifecycle."""

    def setUp(self):
        self.client = Client()

        # Setup Users
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="password",
            role=UserRoles.ADMIN,
        )
        self.librarian = User.objects.create_user(
            username="librarian",
            email="lib@test.com",
            password="password",
            role=UserRoles.LIBRARIAN,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="password",
            role=UserRoles.STUDENT,
        )

        # Setup Book
        self.genre = Genre.objects.create(name="Fiction")
        self.book = Book.objects.create(
            title="Workflow Book",
            description="Desc",
            isbn="9999999999999",
            author="Author",
            publication_date="2023-01-01",
            total_copies=2,
            copies_available=2,
            added_by=self.admin,
        )
        self.book.genre.add(self.genre)

    @patch("book_circulation.views.LibraryEmailService")
    def test_full_borrowing_cycle(self, MockEmailService):
        """
        1. Student requests book (PENDING)
        2. Librarian approves (ISSUED)
        3. Stock decreases
        4. Student returns (RETURN_REQUESTED/RETURNED handling)/Librarian marks returned
        5. Stock increases
        """

        # 1. Student requests book
        self.client.login(username="student", password="password")
        response = self.client.post(
            reverse("borrow_book", kwargs={"book_id": self.book.pk}),
            {"duration_days": 7},
        )

        # Check transaction created
        transaction = Transaction.objects.get(user=self.student, book=self.book)
        self.assertEqual(transaction.status, "PENDING")

        # 2. Librarian approves
        self.client.login(username="librarian", password="password")

        # Verify Pending Request appears in Librarian Dashboard
        response = self.client.get(reverse("librarian_dashboard"))
        self.assertContains(response, "Workflow Book")

        # 3. Simulate Logic (as if View did it) - Testing the result of the action
        transaction.status = "ISSUED"
        transaction.save()

        # Verify Book Availability Decreased
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, 1)

        # Verify Student sees it as borrowed
        self.client.login(username="student", password="password")
        response = self.client.get(reverse("my_books"))
        self.assertContains(response, "Workflow Book")

        # 4. Return
        transaction.mark_as_returned()

        # Verify availability Restored
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, 2)


class RoleAccessTests(TestCase):
    """Verify pages are accessible only to correct roles."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username="a", email="a@t.com", password="p", role=UserRoles.ADMIN
        )
        self.student = User.objects.create_user(
            username="s", email="s@t.com", password="p", role=UserRoles.STUDENT
        )

    def test_admin_dashboard_access(self):
        self.client.login(username="s", password="p")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertNotEqual(response.status_code, 200)  # Should be 403 or redirect

        self.client.login(username="a", password="p")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_logs_access(self):
        self.client.login(username="s", password="p")
        response = self.client.get(reverse("transaction_logs"))
        self.assertNotEqual(response.status_code, 200)

        self.client.login(username="a", password="p")
        response = self.client.get(reverse("transaction_logs"))
        self.assertEqual(response.status_code, 200)
