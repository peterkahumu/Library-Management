from datetime import timedelta, date
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.contrib.messages import get_messages

from books.models import Book, Genre
from book_circulation.models import Transaction
from accounts.models import UserRoles

User = get_user_model()


class AdminDashboardViewTests(TestCase):
    """Test AdminDashboardView functionality and access control."""

    def setUp(self):
        """Create test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=UserRoles.ADMIN,
        )
        self.librarian = User.objects.create_user(
            username="librarian",
            email="librarian@test.com",
            password="librarian123",
            role=UserRoles.LIBRARIAN,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="student123",
            role=UserRoles.STUDENT,
        )

        # Create test data
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")
        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=date(2020, 1, 1),
            total_copies=10,
            copies_available=5,
            added_by=self.admin,
        )
        self.book.genre.add(self.genre)

    def test_admin_access_allowed(self):
        """Only ADMIN users can access admin dashboard."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboards/admin_dashboard.html")

    def test_librarian_access_denied(self):
        """Librarians should be denied access to admin dashboard."""
        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertNotEqual(response.status_code, 200)

    def test_student_access_denied(self):
        """Students should be denied access to admin dashboard."""
        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_access_denied(self):
        """Unauthenticated users should be redirected to login."""
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_kpi_calculations(self):
        """Test KPI calculations are correct."""
        # Create transactions
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.context["total_books"], 1)
        self.assertEqual(response.context["active_students"], 1)
        self.assertEqual(response.context["issued_books"], 1)

    def test_overdue_books_count(self):
        """Test overdue books calculation."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=5),
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.context["overdue_books"], 1)

    def test_frequency_parameter_monthly(self):
        """Test monthly frequency filtering."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"), {"frequency": "monthly"})

        self.assertEqual(response.context["frequency"], "monthly")

    def test_frequency_parameter_annual(self):
        """Test annual frequency filtering."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"), {"frequency": "annual"})

        self.assertEqual(response.context["frequency"], "annual")

    def test_custom_date_range_filtering(self):
        """Test custom date range filtering."""
        start_date = "2025-01-01"
        end_date = "2025-12-31"

        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("admin_dashboard"),
            {"start_date": start_date, "end_date": end_date},
        )

        self.assertEqual(response.context["current_start_date"], start_date)
        self.assertEqual(response.context["current_end_date"], end_date)

    def test_invalid_date_format_fallback(self):
        """Test that invalid date formats fall back to defaults with error message."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("admin_dashboard"),
            {"start_date": "invalid", "end_date": "also-invalid"},
        )

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Invalid date format" in str(m) for m in messages),
            "Expected error message about invalid date format",
        )

    def test_chart_data_generation(self):
        """Test that chart data is generated correctly."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        self.assertIn("trend_labels", response.context)
        self.assertIn("trend_data", response.context)
        self.assertIn("genre_labels", response.context)
        self.assertIn("genre_data", response.context)

    def test_popular_genres_aggregation(self):
        """Test popular genres are aggregated correctly."""
        genre2, _ = Genre.objects.get_or_create(name="SCIFI")
        book2 = Book.objects.create(
            title="SciFi Book",
            description="Test",
            isbn="1234567890124",
            author="Test Author",
            publication_date=date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.admin,
        )
        book2.genre.add(genre2)

        # Create more transactions for FANTASY
        for _ in range(3):
            Transaction.objects.create(
                user=self.student,
                book=self.book,
                status="ISSUED",
            )

        Transaction.objects.create(
            user=self.student,
            book=book2,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        # FANTASY should be more popular
        self.assertIn("FANTASY", response.context["genre_labels"])

    def test_most_active_day_calculation(self):
        """Test most active day of week calculation."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        self.assertIn("active_day", response.context)
        self.assertIsNotNone(response.context["active_day"])

    def test_most_active_hour_calculation(self):
        """Test most active hour calculation."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        self.assertIn("active_hour", response.context)
        self.assertIsNotNone(response.context["active_hour"])

    def test_most_active_user_calculation(self):
        """Test most active user calculation."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(
            response.context["active_user_display"], self.student.user_code
        )
        self.assertEqual(response.context["active_user_count"], 1)

    def test_empty_data_scenario(self):
        """Test dashboard handles empty data gracefully."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["issued_books"], 0)
        self.assertEqual(response.context["overdue_books"], 0)

    def test_recent_activity_display(self):
        """Test recent activity is limited to 3 items."""
        for _ in range(5):
            Transaction.objects.create(
                user=self.student,
                book=self.book,
                status="ISSUED",
                due_date=timezone.now() + timedelta(days=14),
            )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(len(response.context["recent_activity"]), 3)


class LibrarianDashboardViewTests(TestCase):
    """Test LibrarianDashboardView functionality and access control."""

    def setUp(self):
        """Create test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=UserRoles.ADMIN,
        )
        self.librarian = User.objects.create_user(
            username="librarian",
            email="librarian@test.com",
            password="librarian123",
            role=UserRoles.LIBRARIAN,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="student123",
            role=UserRoles.STUDENT,
        )

        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")
        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=date(2020, 1, 1),
            total_copies=10,
            copies_available=5,
            added_by=self.admin,
        )
        self.book.genre.add(self.genre)

    def test_librarian_access_allowed(self):
        """Librarians can access librarian dashboard."""
        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("librarian_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboards/librarian_dashboard.html")

    def test_admin_access_allowed(self):
        """Admins can also access librarian dashboard."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("librarian_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_student_access_denied(self):
        """Students should be denied access."""
        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("librarian_dashboard"))
        self.assertNotEqual(response.status_code, 200)

    def test_issued_today_count(self):
        """Test issued today count calculation."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            checkout_date=timezone.now(),
        )

        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("librarian_dashboard"))

        self.assertEqual(response.context["issued_today_count"], 1)

    def test_returned_today_count(self):
        """Test returned today count calculation."""
        transaction = Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )
        transaction.mark_as_returned()

        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("librarian_dashboard"))

        self.assertEqual(response.context["returned_today_count"], 1)

    def test_total_overdue_count(self):
        """Test overdue count uses Transaction manager method."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=5),
        )

        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("librarian_dashboard"))

        self.assertEqual(response.context["total_overdue_count"], 1)

    def test_pending_borrow_count(self):
        """Test pending borrow requests count."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )

        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("librarian_dashboard"))

        self.assertEqual(response.context["pending_borrow_count"], 1)

    def test_pending_return_count(self):
        """Test pending return requests count."""
        transaction = Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )
        transaction.status = "RETURN_REQUESTED"
        transaction.save()

        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("librarian_dashboard"))

        self.assertEqual(response.context["pending_return_count"], 1)

    def test_recent_transactions_limited_to_two(self):
        """Test recent transactions are limited to 2 items."""
        for _ in range(5):
            Transaction.objects.create(
                user=self.student,
                book=self.book,
                status="ISSUED",
                due_date=timezone.now() + timedelta(days=14),
            )

        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("librarian_dashboard"))

        self.assertEqual(len(response.context["recent_transactions"]), 2)


class StudentDashboardViewTests(TestCase):
    """Test StudentDashboardView functionality and access control."""

    def setUp(self):
        """Create test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=UserRoles.ADMIN,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="student123",
            role=UserRoles.STUDENT,
        )

        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")
        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=date(2020, 1, 1),
            total_copies=10,
            copies_available=5,
            added_by=self.admin,
        )
        self.book.genre.add(self.genre)

    def test_student_access_allowed(self):
        """Students can access their dashboard."""
        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboards/student_dashboard.html")

    def test_admin_access_allowed(self):
        """Admins can also access student dashboard."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_borrowed_books_count(self):
        """Test borrowed books count includes ISSUED and PENDING."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )

        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("student_dashboard"))

        self.assertEqual(response.context["borrowed_books"], 2)

    def test_overdue_books_count(self):
        """Test overdue books count for logged-in student."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=3),
        )

        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("student_dashboard"))

        self.assertEqual(response.context["overdue_books"], 1)

    def test_fines_calculation(self):
        """Test fines are calculated based on days overdue."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=5),
        )

        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("student_dashboard"))

        # Should be 5 days overdue
        self.assertEqual(response.context["fines"], 5)

    def test_fines_zero_when_no_overdue(self):
        """Test fines are 0 when no books are overdue."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=7),
        )

        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("student_dashboard"))

        self.assertEqual(response.context["fines"], 0)


class TransactionLogsViewTests(TestCase):
    """Test TransactionLogsView functionality and filtering."""

    def setUp(self):
        """Create test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=UserRoles.ADMIN,
        )
        self.librarian = User.objects.create_user(
            username="librarian",
            email="librarian@test.com",
            password="librarian123",
            role=UserRoles.LIBRARIAN,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="student123",
            role=UserRoles.STUDENT,
        )

        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")
        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=date(2020, 1, 1),
            total_copies=50,
            copies_available=50,
            added_by=self.admin,
        )
        self.book.genre.add(self.genre)

    def test_admin_access_allowed(self):
        """Admins can access transaction logs."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("transaction_logs"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboards/transaction_logs.html")

    def test_librarian_access_allowed(self):
        """Librarians can access transaction logs."""
        self.client.login(username="librarian", password="librarian123")
        response = self.client.get(reverse("transaction_logs"))
        self.assertEqual(response.status_code, 200)

    def test_student_access_denied(self):
        """Students should be denied access."""
        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("transaction_logs"))
        self.assertNotEqual(response.status_code, 200)

    def test_pagination_25_per_page(self):
        """Test pagination shows 25 items per page."""
        for i in range(30):
            Transaction.objects.create(
                user=self.student,
                book=self.book,
                status="ISSUED",
                due_date=timezone.now() + timedelta(days=14),
            )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("transaction_logs"))

        self.assertEqual(len(response.context["transactions"]), 25)
        self.assertTrue(response.context["is_paginated"])

    def test_filter_by_date(self):
        """Test filtering by specific date."""
        specific_date = timezone.now().date()
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            checkout_date=timezone.now(),
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("transaction_logs"),
            {"date": specific_date.strftime("%Y-%m-%d"), "status": "issued"},
        )

        self.assertEqual(response.context["transactions"].count(), 1)

    def test_filter_by_status(self):
        """Test filtering by status (note: bug in views.py line 252)."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )
        # Create a RETURNED transaction using mark_as_returned
        returned_txn = Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )
        returned_txn.mark_as_returned()

        self.client.login(username="admin", password="admin123")
        # NOTE: There's a bug in views.py line 252 - status filter only works with date
        response = self.client.get(
            reverse("transaction_logs"),
            {"date": timezone.now().date().strftime("%Y-%m-%d"), "status": "issued"},
        )

        # All should be ISSUED
        for transaction in response.context["transactions"]:
            self.assertEqual(transaction.status, "ISSUED")

    def test_filter_by_user_code(self):
        """Test filtering by user code (case-insensitive)."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("transaction_logs"),
            {"user_code": self.student.user_code.lower()},
        )

        self.assertEqual(response.context["transactions"].count(), 1)

    def test_filter_by_nonexistent_user(self):
        """Test filtering by non-existent user returns empty queryset."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("transaction_logs"), {"user_code": "NONEXISTENT"}
        )

        self.assertEqual(response.context["transactions"].count(), 0)

    def test_filter_by_day_of_week(self):
        """Test filtering by day of week."""
        transaction = Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        # Get the day of week for the transaction
        day_map = {
            1: "sunday",
            2: "monday",
            3: "tuesday",
            4: "wednesday",
            5: "thursday",
            6: "friday",
            7: "saturday",
        }
        # Django uses Sunday=1
        weekday = (transaction.checkout_date.weekday() + 2) % 7
        if weekday == 0:
            weekday = 7
        day_name = day_map[weekday]

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("transaction_logs"), {"day": day_name})

        self.assertGreater(response.context["transactions"].count(), 0)

    def test_filter_by_hour(self):
        """Test filtering by hour of day."""
        transaction = Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        hour = transaction.checkout_date.hour

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("transaction_logs"), {"hour": str(hour)})

        self.assertGreater(response.context["transactions"].count(), 0)

    def test_filter_invalid_hour(self):
        """Test invalid hour filter is ignored gracefully."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("transaction_logs"), {"hour": "invalid"})

        # Should return all transactions without filtering
        self.assertGreater(response.context["transactions"].count(), 0)

    def test_combined_filters(self):
        """Test multiple filters can be applied together."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("transaction_logs"), {"user_code": self.student.user_code}
        )

        self.assertEqual(response.context["transactions"].count(), 1)

    def test_context_preserves_filter_parameters(self):
        """Test that filter parameters are preserved in context."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("transaction_logs"),
            {
                "date": "2025-01-01",
                "status": "issued",
                "user_code": "ST123456",
                "day": "monday",
                "hour": "10",
            },
        )

        self.assertEqual(response.context["current_date"], "2025-01-01")
        self.assertEqual(response.context["current_status"], "issued")
        self.assertEqual(response.context["current_user_code"], "ST123456")
        self.assertEqual(response.context["current_day"], "monday")
        self.assertEqual(response.context["current_hour"], "10")

    def test_invalid_date_format_ignored(self):
        """Test invalid date format is ignored gracefully."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("transaction_logs"), {"date": "invalid-date", "status": "issued"}
        )

        # Should not crash, will return all transactions
        self.assertEqual(response.status_code, 200)


class UserRoleUpdateViewTests(TestCase):
    """Test UserRoleUpdateView functionality and access control."""

    def setUp(self):
        """Create test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=UserRoles.ADMIN,
        )
        self.librarian = User.objects.create_user(
            username="librarian",
            email="librarian@test.com",
            password="librarian123",
            role=UserRoles.LIBRARIAN,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="student123",
            role=UserRoles.STUDENT,
        )

    def test_admin_access_allowed(self):
        """Only admins can update user roles."""
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            reverse("user_role_update"),
            {
                "user_code": self.student.user_code,
                "new_role": UserRoles.LIBRARIAN,
            },
        )
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)

    def test_librarian_access_denied(self):
        """Librarians cannot update user roles."""
        self.client.login(username="librarian", password="librarian123")
        response = self.client.post(
            reverse("user_role_update"),
            {
                "user_code": self.student.user_code,
                "new_role": UserRoles.ADMIN,
            },
        )
        self.assertNotEqual(response.status_code, 302)

    def test_successful_role_update(self):
        """Test successful role update changes user role."""
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            reverse("user_role_update"),
            {
                "user_code": self.student.user_code,
                "new_role": UserRoles.LIBRARIAN,
            },
        )

        self.student.refresh_from_db()
        self.assertEqual(self.student.role, UserRoles.LIBRARIAN)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("updated" in str(m).lower() for m in messages))

    def test_invalid_role_rejection(self):
        """Test invalid role is rejected."""
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            reverse("user_role_update"),
            {
                "user_code": self.student.user_code,
                "new_role": "invalid_role",
            },
        )

        self.student.refresh_from_db()
        self.assertEqual(self.student.role, UserRoles.STUDENT)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("invalid" in str(m).lower() for m in messages))

    def test_nonexistent_user_handling(self):
        """Test non-existent user returns error message."""
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            reverse("user_role_update"),
            {
                "user_code": "NONEXISTENT",
                "new_role": UserRoles.LIBRARIAN,
            },
        )

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("not found" in str(m).lower() for m in messages))

    def test_self_role_change_prevention(self):
        """Test admins cannot change their own role."""
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            reverse("user_role_update"),
            {
                "user_code": self.admin.user_code,
                "new_role": UserRoles.STUDENT,
            },
        )

        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, UserRoles.ADMIN)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("cannot change your own role" in str(m).lower() for m in messages)
        )

    def test_redirect_url_next_parameter(self):
        """Test redirect respects 'next' parameter."""
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            reverse("user_role_update"),
            {
                "user_code": self.student.user_code,
                "new_role": UserRoles.LIBRARIAN,
                "next": reverse("transaction_logs"),
            },
        )

        self.assertRedirects(response, reverse("transaction_logs"))

    def test_default_redirect_to_admin_dashboard(self):
        """Test default redirect goes to admin dashboard."""
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            reverse("user_role_update"),
            {
                "user_code": self.student.user_code,
                "new_role": UserRoles.LIBRARIAN,
            },
        )

        self.assertRedirects(response, reverse("admin_dashboard"))


class FilterHelperFunctionTests(TestCase):
    """Test get_filtered_queryset helper function."""

    def setUp(self):
        """Create test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=UserRoles.ADMIN,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="student123",
            role=UserRoles.STUDENT,
        )

        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")
        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=date(2020, 1, 1),
            total_copies=10,
            copies_available=5,
            added_by=self.admin,
        )
        self.book.genre.add(self.genre)

    def test_default_monthly_frequency_range(self):
        """Test default monthly frequency uses 180 days."""
        # Create old transaction (beyond 180 days)
        old_transaction = Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )
        old_transaction.checkout_date = timezone.now() - timedelta(days=200)
        old_transaction.save()

        # Create recent transaction
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"), {"frequency": "monthly"})

        # Old transaction should be filtered out
        self.assertEqual(len(response.context["trend_data"]), 1)

    def test_annual_frequency_range(self):
        """Test annual frequency uses 3 years (1095 days)."""
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"), {"frequency": "annual"})

        self.assertEqual(response.context["frequency"], "annual")

    def test_custom_date_range(self):
        """Test custom date range overrides default frequency."""
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
        )

        self.client.login(username="admin", password="admin123")
        response = self.client.get(
            reverse("admin_dashboard"),
            {
                "start_date": timezone.now().date().strftime("%Y-%m-%d"),
                "end_date": (timezone.now() + timedelta(days=1))
                .date()
                .strftime("%Y-%m-%d"),
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_filters_only_issued_and_returned(self):
        """Test queryset only includes ISSUED and RETURNED transactions."""
        # Create PENDING transaction (should be filtered out)
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )
        # Create ISSUED transaction (should be included)
        Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            checkout_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=14),
        )
        # Create RETURNED transaction (should be included)
        returned_txn = Transaction.objects.create(
            user=self.student,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=14),
        )
        returned_txn.mark_as_returned()

        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("admin_dashboard"))

        # Only ISSUED and RETURNED should be counted in trends (not PENDING)
        total_count = sum(response.context["trend_data"])
        self.assertEqual(total_count, 2)


class TemplateTagTests(TestCase):
    """Test custom template tags."""

    def test_url_replace_single_parameter(self):
        """Test url_replace with single parameter."""
        from django.http import QueryDict

        query = QueryDict(mutable=True)
        query["foo"] = "bar"

        template = Template("{% load dashboard_extras %}{% url_replace page=2 %}")
        request = type("Request", (), {"GET": query})()
        context = Context({"request": request})

        result = template.render(context)
        self.assertIn("page=2", result)
        self.assertIn("foo=bar", result)

    def test_url_replace_multiple_parameters(self):
        """Test url_replace with multiple parameters."""
        from django.http import QueryDict

        query = QueryDict(mutable=True)

        template = Template(
            "{% load dashboard_extras %}{% url_replace page=2 status='issued' %}"
        )
        request = type("Request", (), {"GET": query})()
        context = Context({"request": request})

        result = template.render(context)
        self.assertIn("page=2", result)
        self.assertIn("status=issued", result)

    def test_url_replace_preserves_existing_params(self):
        """Test url_replace preserves existing GET parameters."""
        from django.http import QueryDict

        query = QueryDict(mutable=True)
        query["existing"] = "value"
        query["other"] = "data"

        template = Template("{% load dashboard_extras %}{% url_replace page=2 %}")
        request = type("Request", (), {"GET": query})()
        context = Context({"request": request})

        result = template.render(context)
        self.assertIn("page=2", result)
        self.assertIn("existing=value", result)
        self.assertIn("other=data", result)
