import datetime
from datetime import timedelta
from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction

from books.models import Book, Genre
from .models import Transaction

User = get_user_model()


class TransactionModelTests(TestCase):
    """Test Transaction model creation, validation, and basic functionality."""

    def setUp(self):
        """Create test fixtures for transaction tests."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

        self.book = Book.objects.create(
            title="Test Book",
            description="Test description",
            isbn="1234567890123",
            author="Test Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        self.book.genre.add(self.genre)

    def test_transaction_creation_with_issued_status(self):
        """
        Creating a transaction with ISSUED status should:
        - Decrement book's copies_available
        - Set checkout_date automatically
        - Auto-set due_date to 14 days from now
        """
        initial_available = self.book.copies_available

        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, initial_available - 1)
        self.assertIsNotNone(transaction.checkout_date)
        self.assertIsNotNone(transaction.due_date)
        expected_due = timezone.now() + timedelta(days=14)
        self.assertAlmostEqual(
            transaction.due_date.timestamp(), expected_due.timestamp(), delta=2
        )

    def test_transaction_creation_with_pending_status(self):
        """
        Creating a transaction with PENDING status should not decrement stock.
        """
        initial_available = self.book.copies_available

        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )

        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, initial_available)
        self.assertEqual(transaction.status, "PENDING")

    def test_transaction_for_ebook_does_not_decrement_stock(self):
        """
        Creating a transaction for an ebook should not affect stock levels.
        """
        initial_available = self.book.copies_available

        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            is_ebook=True,
        )

        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, initial_available)
        self.assertTrue(transaction.is_ebook)

    def test_transaction_string_representation(self):
        """
        Transaction __str__ should return format: 'user@email - BookTitle (Status)'.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        expected = f"{self.user.email} - {self.book.title} (Issued)"
        self.assertEqual(str(transaction), expected)

    def test_transaction_repr(self):
        """
        Transaction __repr__ should return format for debugging.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        expected = f"<Transaction: {transaction.pk} - {self.book.title} - ISSUED>"
        self.assertEqual(repr(transaction), expected)


class TransactionValidationTests(TestCase):
    """Test Transaction model validation and clean() method."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        self.book.genre.add(self.genre)

    def test_due_date_must_be_after_checkout_date(self):
        """
        Validation should fail if due_date is before or equal to checkout_date.
        """
        transaction = Transaction(
            user=self.user,
            book=self.book,
            status="PENDING",
            checkout_date=timezone.now(),
            due_date=timezone.now() - timedelta(days=1),
        )

        with self.assertRaises(ValidationError) as context:
            transaction.clean()

        self.assertIn("due_date", context.exception.message_dict)

    def test_returned_date_must_be_after_checkout_date(self):
        """
        Validation should fail if returned_date is before checkout_date.
        """
        checkout = timezone.now()
        transaction = Transaction(
            user=self.user,
            book=self.book,
            status="RETURNED",
            checkout_date=checkout,
            due_date=checkout + timedelta(days=14),
            returned_date=checkout - timedelta(days=1),
        )

        with self.assertRaises(ValidationError) as context:
            transaction.clean()

        self.assertIn("returned_date", context.exception.message_dict)

    def test_returned_date_requires_returned_status(self):
        """
        Validation should fail if returned_date is set but status is not RETURNED.
        """
        checkout = timezone.now() - timedelta(days=5)
        transaction = Transaction(
            user=self.user,
            book=self.book,
            status="ISSUED",
            checkout_date=checkout,
            due_date=checkout + timedelta(days=14),
            returned_date=timezone.now(),
        )

        with self.assertRaises(ValidationError) as context:
            transaction.clean()

        self.assertIn("status", context.exception.message_dict)

    def test_invalid_status_transition_issued_to_pending(self):
        """
        Status transitions must follow allowed paths.
        ISSUED → PENDING is invalid.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        transaction.status = "PENDING"

        with self.assertRaises(ValidationError) as context:
            transaction.clean()

        self.assertIn("status", context.exception.message_dict)

    def test_valid_status_transition_pending_to_issued(self):
        """
        PENDING → ISSUED is a valid status transition.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )

        transaction.status = "ISSUED"

        try:
            transaction.clean()
        except ValidationError:
            self.fail("PENDING to ISSUED should be a valid transition")

    def test_valid_status_transition_issued_to_returned(self):
        """
        ISSUED → RETURNED is a valid status transition.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        transaction.status = "RETURNED"
        transaction.returned_date = timezone.now()

        try:
            transaction.clean()
        except ValidationError:
            self.fail("ISSUED to RETURNED should be a valid transition")

    def test_returned_status_is_final(self):
        """
        Once status is RETURNED, it cannot transition to any other status.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )
        transaction.status = "RETURNED"
        transaction.returned_date = timezone.now()
        transaction.save()

        transaction.status = "ISSUED"

        with self.assertRaises(ValidationError) as context:
            transaction.clean()

        self.assertIn("status", context.exception.message_dict)


class TransactionStatusTransitionTests(TestCase):
    """Test status transitions and their effects on book stock."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        self.book.genre.add(self.genre)

    def test_pending_to_issued_decrements_stock(self):
        """
        Transitioning from PENDING to ISSUED should decrement book stock.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )

        initial_available = self.book.copies_available

        transaction.status = "ISSUED"
        transaction.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, initial_available - 1)

    def test_issued_to_returned_increments_stock(self):
        """
        Transitioning from ISSUED to RETURNED should increment book stock
        and auto-set returned_date.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        self.book.refresh_from_db()
        available_after_issue = self.book.copies_available

        transaction.status = "RETURNED"
        transaction.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, available_after_issue + 1)
        self.assertIsNotNone(transaction.returned_date)

    def test_cannot_issue_when_no_copies_available(self):
        """
        Raise validation error for unavailable book.
        """
        self.book.copies_available = 0
        self.book.save()

        with self.assertRaises(ValidationError) as context:
            Transaction.objects.create(
                user=self.user,
                book=self.book,
                status="ISSUED",
            )

        self.assertIn("not available", str(context.exception).lower())

    def test_cannot_return_when_all_copies_available(self):
        """
        Attempting to return a book when all copies are already available
        should raise ValidationError.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        self.book.copies_available = self.book.total_copies
        self.book.save()

        transaction.status = "RETURNED"

        with self.assertRaises(ValidationError):
            transaction.save()


class TransactionHelperMethodTests(TestCase):
    """Test Transaction helper methods and properties."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        self.book.genre.add(self.genre)

    def test_is_overdue_property_for_current_transaction(self):
        """
        is_overdue should return True when current time exceeds due_date.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=1),
        )

        self.assertTrue(transaction.is_overdue)

    def test_is_overdue_property_for_on_time_transaction(self):
        """
        is_overdue should return False when due_date is in the future.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=7),
        )

        self.assertFalse(transaction.is_overdue)

    def test_is_overdue_property_for_returned_transaction(self):
        """
        is_overdue should return False for RETURNED transactions regardless of dates.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=5),
        )
        transaction.status = "RETURNED"
        transaction.save()

        self.assertFalse(transaction.is_overdue)

    def test_days_overdue_calculation(self):
        """
        days_overdue should return correct number of days past due_date.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=3),
        )

        self.assertEqual(transaction.days_overdue, 3)

    def test_days_overdue_for_on_time_transaction(self):
        """
        days_overdue should return 0 for transactions not yet overdue.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=7),
        )

        self.assertEqual(transaction.days_overdue, 0)

    def test_borrowing_period_days_for_active_transaction(self):
        """
        borrowing_period_days should calculate days since checkout
        """
        past_checkout = timezone.now() - timedelta(days=5)
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=9),
        )
        transaction.checkout_date = past_checkout
        transaction.save()

        self.assertEqual(transaction.borrowing_period_days, 5)

    def test_borrowing_period_days_for_returned_transaction(self):
        """
        borrowing_period_days should use returned_date for returned transactions.
        """
        checkout = timezone.now() - timedelta(days=10)
        returned = timezone.now() - timedelta(days=3)

        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=4),
        )
        transaction.checkout_date = checkout
        transaction.save()

        transaction.status = "RETURNED"
        transaction.returned_date = returned
        transaction.save()

        self.assertEqual(transaction.borrowing_period_days, 7)

    def test_mark_as_returned_method(self):
        """
        mark_as_returned() should change status to RETURNED, set returned_date,
        and increment book stock.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        self.book.refresh_from_db()
        available_after_issue = self.book.copies_available

        result = transaction.mark_as_returned()

        self.assertTrue(result)
        self.assertEqual(transaction.status, "RETURNED")
        self.assertIsNotNone(transaction.returned_date)

        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, available_after_issue + 1)

    def test_mark_as_returned_for_already_returned(self):
        """
        mark_as_returned() should return False if already returned.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )
        transaction.mark_as_returned()

        result = transaction.mark_as_returned()

        self.assertFalse(result)

    def test_extend_due_date_method(self):
        """
        extend_due_date() should add specified days to due_date.
        """
        original_due = timezone.now() + timedelta(days=14)
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
            due_date=original_due,
        )

        transaction.extend_due_date(days=7)

        expected_due = original_due + timedelta(days=7)
        self.assertAlmostEqual(
            transaction.due_date.timestamp(), expected_due.timestamp(), delta=1
        )

    def test_extend_due_date_raises_for_returned_transaction(self):
        """
        extend_due_date() should raise ValidationError for RETURNED transactions.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )
        transaction.mark_as_returned()

        with self.assertRaises(ValidationError) as context:
            transaction.extend_due_date(days=7)

        self.assertIn("issued", str(context.exception).lower())


class TransactionManagerTests(TestCase):
    """Test TransactionManager custom query methods."""

    def setUp(self):
        """Create test fixtures with multiple transactions."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

        self.book1 = Book.objects.create(
            title="Book 1",
            description="Test",
            isbn="1111111111111",
            author="Author 1",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user1,
        )
        self.book1.genre.add(self.genre)

        self.book2 = Book.objects.create(
            title="Book 2",
            description="Test",
            isbn="2222222222222",
            author="Author 2",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user1,
        )
        self.book2.genre.add(self.genre)

    def test_active_transactions_filter(self):
        """
        active() should return only PENDING and ISSUED transactions.
        """
        pending = Transaction.objects.create(
            user=self.user1,
            book=self.book1,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )
        issued = Transaction.objects.create(
            user=self.user1,
            book=self.book2,
            status="ISSUED",
        )
        returned = Transaction.objects.create(
            user=self.user2,
            book=self.book1,
            status="ISSUED",
        )
        returned.mark_as_returned()

        active = Transaction.objects.active()

        self.assertEqual(active.count(), 2)
        self.assertIn(pending, active)
        self.assertIn(issued, active)
        self.assertNotIn(returned, active)

    def test_overdue_transactions_filter(self):
        """
        overdue() should return only ISSUED transactions past their due_date.
        """
        overdue = Transaction.objects.create(
            user=self.user1,
            book=self.book1,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=1),
        )
        on_time = Transaction.objects.create(
            user=self.user1,
            book=self.book2,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=7),
        )
        pending = Transaction.objects.create(
            user=self.user2,
            book=self.book1,
            status="PENDING",
            due_date=timezone.now() - timedelta(days=1),
        )

        overdue_transactions = Transaction.objects.overdue()

        self.assertEqual(overdue_transactions.count(), 1)
        self.assertIn(overdue, overdue_transactions)
        self.assertNotIn(on_time, overdue_transactions)
        self.assertNotIn(pending, overdue_transactions)

    def test_for_user_filter(self):
        """
        for_user() should return transactions for specific user with optimized queries.
        """
        trans1 = Transaction.objects.create(
            user=self.user1,
            book=self.book1,
            status="ISSUED",
        )
        trans2 = Transaction.objects.create(
            user=self.user1,
            book=self.book2,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )
        trans3 = Transaction.objects.create(
            user=self.user2,
            book=self.book1,
            status="ISSUED",
        )

        user1_transactions = Transaction.objects.for_user(self.user1)

        self.assertEqual(user1_transactions.count(), 2)
        self.assertIn(trans1, user1_transactions)
        self.assertIn(trans2, user1_transactions)
        self.assertNotIn(trans3, user1_transactions)

    def test_for_book_filter(self):
        """
        for_book() should return transactions for specific book with optimized queries.
        """
        trans1 = Transaction.objects.create(
            user=self.user1,
            book=self.book1,
            status="ISSUED",
        )
        trans2 = Transaction.objects.create(
            user=self.user2,
            book=self.book1,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )
        trans3 = Transaction.objects.create(
            user=self.user1,
            book=self.book2,
            status="ISSUED",
        )

        book1_transactions = Transaction.objects.for_book(self.book1)

        self.assertEqual(book1_transactions.count(), 2)
        self.assertIn(trans1, book1_transactions)
        self.assertIn(trans2, book1_transactions)
        self.assertNotIn(trans3, book1_transactions)

    def test_returned_on_time_filter(self):
        """
        returned_on_time() should return transactions returned before or on due_date.
        """
        on_time = Transaction.objects.create(
            user=self.user1,
            book=self.book1,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=14),
        )
        on_time.status = "RETURNED"
        on_time.returned_date = on_time.due_date - timedelta(days=1)
        on_time.save()

        late = Transaction.objects.create(
            user=self.user1,
            book=self.book2,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=7),
        )
        late.mark_as_returned()

        on_time_transactions = Transaction.objects.returned_on_time()

        self.assertEqual(on_time_transactions.count(), 1)
        self.assertIn(on_time, on_time_transactions)
        self.assertNotIn(late, on_time_transactions)

    def test_returned_late_filter(self):
        """
        returned_late() should return transactions returned after due_date.
        """
        late = Transaction.objects.create(
            user=self.user1,
            book=self.book1,
            status="ISSUED",
            due_date=timezone.now() - timedelta(days=7),
        )
        late.mark_as_returned()

        on_time = Transaction.objects.create(
            user=self.user1,
            book=self.book2,
            status="ISSUED",
            due_date=timezone.now() + timedelta(days=14),
        )
        on_time.status = "RETURNED"
        on_time.returned_date = on_time.due_date - timedelta(days=1)
        on_time.save()

        late_transactions = Transaction.objects.returned_late()

        self.assertEqual(late_transactions.count(), 1)
        self.assertIn(late, late_transactions)
        self.assertNotIn(on_time, late_transactions)


class TransactionRaceConditionTests(TransactionTestCase):
    """Test race condition prevention in concurrent transaction operations."""

    def setUp(self):
        """Create test fixtures."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

        self.book = Book.objects.create(
            title="Last Copy Book",
            description="Test",
            isbn="1234567890123",
            author="Test Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=1,
            copies_available=1,
            added_by=self.user1,
        )
        self.book.genre.add(self.genre)

    def test_concurrent_checkout_prevents_overbooking(self):
        """
        When two users try to checkout the last copy simultaneously,
        only one should succeed due to select_for_update().
        """
        from threading import Thread

        results = []

        def checkout_book(user):
            try:
                with db_transaction.atomic():
                    Transaction.objects.create(
                        user=user,
                        book=self.book,
                        status="ISSUED",
                    )
                    results.append(("success", user.username))
            except (ValidationError, Exception) as e:
                results.append(("failed", user.username, str(e)))

        thread1 = Thread(target=checkout_book, args=(self.user1,))
        thread2 = Thread(target=checkout_book, args=(self.user2,))

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        success_count = sum(1 for r in results if r[0] == "success")
        self.assertEqual(
            success_count, 1, "Only one user should successfully checkout the last copy"
        )

        self.book.refresh_from_db()
        self.assertEqual(
            self.book.copies_available,
            0,
            "Book should have 0 copies available after single checkout",
        )
