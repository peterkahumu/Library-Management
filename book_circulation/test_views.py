from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from accounts.models import UserRoles
from books.models import Book, Genre
from book_circulation.models import Transaction

User = get_user_model()

class BookCirculationViewTests(TestCase):
    """Tests for views in book_circulation app."""

    def setUp(self):
        self.client = Client()
        
        # Users
        self.admin = User.objects.create_user(
            username="admin", email="admin@test.com", password="password", role=UserRoles.ADMIN
        )
        self.librarian = User.objects.create_user(
            username="librarian", email="lib@test.com", password="password", role=UserRoles.LIBRARIAN
        )
        self.student = User.objects.create_user(
            username="student", email="student@test.com", password="password", role=UserRoles.STUDENT
        )
        
        # Book
        self.genre = Genre.objects.create(name="Fiction")
        self.book = Book.objects.create(
            title="View Test Book",
            description="Desc",
            isbn="1112223334445",
            author="Author",
            publication_date="2023-01-01",
            total_copies=2,
            copies_available=2,
            added_by=self.admin
        )
        self.book.genre.add(self.genre)

    def test_borrow_book_view_get(self):
        """Test GET request to borrow confirm page."""
        self.client.login(username="student", password="password")
        response = self.client.get(reverse("borrow_book", kwargs={"book_id": self.book.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "circulation/borrow_confirm.html")
        self.assertEqual(response.context["book"], self.book)

    def test_borrow_book_view_not_available(self):
        """Test redirection when book is not available."""
        self.book.copies_available = 0
        self.book.save()
        
        self.client.login(username="student", password="password")
        response = self.client.get(reverse("borrow_book", kwargs={"book_id": self.book.pk}))
        
        self.assertEqual(response.status_code, 302)
        # Should redirect to book detail
        self.assertIn(f"/books/{self.book.pk}/", response.url)

    def test_borrow_book_view_already_borrowed(self):
        """Test redirection when user already has active transaction."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username="student", password="password")
        response = self.client.get(reverse("borrow_book", kwargs={"book_id": self.book.pk}))
        
        self.assertEqual(response.status_code, 302)
        
    @patch("book_circulation.views.LibraryEmailService")
    def test_borrow_book_submit_physical(self, MockEmail):
        """Test submitting borrow form for physical book."""
        self.client.login(username="student", password="password")
        response = self.client.post(
            reverse("borrow_book", kwargs={"book_id": self.book.pk}),
            {"duration_days": 14}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaction.objects.filter(user=self.student, book=self.book, status="PENDING").exists())
        MockEmail.send_borrow_request_confirmation.assert_called_once()

    @patch("book_circulation.views.LibraryEmailService")
    def test_borrow_book_submit_ebook(self, MockEmail):
        """Test submitting borrow form for ebook."""
        self.book.format = "EBOOK"
        self.book.save()
        
        self.client.login(username="student", password="password")
        response = self.client.post(
            reverse("borrow_book", kwargs={"book_id": self.book.pk}),
            {"duration_days": 14}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaction.objects.filter(user=self.student, book=self.book, status="DOWNLOADED").exists())
        MockEmail.send_book_issued_notification.assert_called_once()
        
    def test_my_books_list_view(self):
        """Test My Books page renders correctly with context."""
        # Create various transactions
        t1 = Transaction.objects.create(
            user=self.student, 
            book=self.book, 
            status="PENDING",
            due_date=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username="student", password="password")
        response = self.client.get(reverse("my_books"))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(t1, response.context["pending_requests"])

    @patch("book_circulation.views.LibraryEmailService")
    def test_request_return_view(self, MockEmail):
        """Test user requesting a return."""
        t1 = Transaction.objects.create(
            user=self.student, 
            book=self.book, 
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username="student", password="password")
        response = self.client.post(reverse("request_return", kwargs={"pk": t1.pk}))
        
        t1.refresh_from_db()
        self.assertEqual(t1.status, "RETURN_REQUESTED")
        self.assertEqual(response.status_code, 302)

    # Librarian View Tests
    
    def test_librarian_dashboard_access(self):
        """Test access control for librarian views."""
        url = reverse("librarian_borrow_requests")
        
        # Student -> Fail
        self.client.login(username="student", password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Librarian -> Success
        self.client.login(username="librarian", password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @patch("book_circulation.views.LibraryEmailService")
    def test_approve_borrow(self, MockEmail):
        """Test librarian approving borrow request."""
        t1 = Transaction.objects.create(
            user=self.student, 
            book=self.book, 
            status="PENDING",
            due_date=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username="librarian", password="password")
        response = self.client.post(reverse("approve_borrow", kwargs={"pk": t1.pk}))
        
        t1.refresh_from_db()
        self.assertEqual(t1.status, "ISSUED")
        self.assertEqual(response.status_code, 302)

    @patch("book_circulation.views.LibraryEmailService")
    def test_reject_borrow(self, MockEmail):
        """Test librarian rejecting borrow request."""
        t1 = Transaction.objects.create(
            user=self.student, 
            book=self.book, 
            status="PENDING",
            due_date=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username="librarian", password="password")
        response = self.client.post(reverse("reject_borrow", kwargs={"pk": t1.pk}))
        
        self.assertFalse(Transaction.objects.filter(pk=t1.pk).exists())
        self.assertEqual(response.status_code, 302)

    @patch("book_circulation.views.LibraryEmailService")
    def test_approve_return(self, MockEmail):
        """Test librarian approving return."""
        # Decrease stock manually to simulate book being out
        self.book.copies_available -= 1
        self.book.save()
        
        t1 = Transaction.objects.create(
            user=self.student, 
            book=self.book, 
            status="RETURN_REQUESTED",
            due_date=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username="librarian", password="password")
        response = self.client.post(reverse("approve_return", kwargs={"pk": t1.pk}))
        
        t1.refresh_from_db()
        self.assertEqual(t1.status, "RETURNED")

    @patch("book_circulation.views.LibraryEmailService")
    def test_reject_return(self, MockEmail):
        """Test librarian rejecting return (reverting to ISSUED)."""
        t1 = Transaction.objects.create(
            user=self.student, 
            book=self.book, 
            status="RETURN_REQUESTED",
            due_date=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username="librarian", password="password")
        response = self.client.post(reverse("reject_return", kwargs={"pk": t1.pk}))
        
        t1.refresh_from_db()
        self.assertEqual(t1.status, "ISSUED")
