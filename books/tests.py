from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

import uuid
from datetime import date, datetime
from .models import Book, Genre


class BookModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up reusable test data for all test cases."""
        User = get_user_model()

        cls.user = User.objects.create_user(
            username="testuser",
            email="testuser.test.com",
            password="TestUser1234",
        )

        cls.genre = Genre.objects.get(name="ADVENTURE")
        cls.genre1 = Genre.objects.get(name="COMIC")

        cls.book = Book.objects.create(
            title="Test Book",
            description="Test Book description",
            author="Test Author",
            isbn="1234567890",
            publication_date=date(2000, 1, 31),
            edition="First",
            language="en",
            added_by=cls.user,
        )

        cls.book.genre.set([cls.genre, cls.genre1])

    def test_book_fields(self):
        """Verify that all book fields are stored and retrieved correctly."""
        self.assertEqual(self.book.title, "Test Book")
        self.assertEqual(self.book.description, "Test Book description")
        self.assertEqual(self.book.author, "Test Author")
        self.assertEqual(self.book.publication_date, date(year=2000, month=1, day=31))
        self.assertEqual(self.book.added_by, self.user)
        self.assertEqual(self.book.language, "en")
        self.assertEqual(self.book.isbn, "1234567890")
        self.assertIn(self.genre, self.book.genre.all())
        self.assertIn(self.genre1, self.book.genre.all())

    def test_mandatory_fields(self):
        """Check that missing mandatory fields raise validation errors."""
        book = Book()
        with self.assertRaises(ValidationError) as cm:
            book.full_clean()
        errors = cm.exception.message_dict
        self.assertIn("title", errors)
        self.assertIn("description", errors)
        self.assertIn("isbn", errors)
        self.assertIn("author", errors)
        self.assertIn("publication_date", errors)

    def test_default_fields(self):
        """Confirm default values (language, copies)
        are applied when not explicitly set."""
        book = Book.objects.create(
            title="Test book",
            description="Test description",
            isbn=1234567891,
            author="Test author",
            publication_date=date(2000, 1, 31),
            added_by=self.user,
        )
        book.genre.set([self.genre])
        self.assertEqual(book.language, "en")
        self.assertEqual(book.copies_available, 1)
        self.assertEqual(book.total_copies, 1)

    def test_unique_isbn(self):
        """Ensure duplicate ISBNs raise a validation error."""
        with self.assertRaises(ValidationError):
            Book.objects.create(
                title="Test book",
                description="Test description",
                isbn="1234567890",
                author="Test author",
                publication_date=date(2000, 1, 31),
                added_by=self.user,
            )

    def test_unique_id(self):
        """Verify that book_id is unique and cannot be reused."""
        book = Book.objects.create(
            title="Test Title",
            description="Description",
            author="Test Author",
            isbn="1298987974",
            publication_date=date(2000, 1, 1),
            added_by=self.user,
        )
        self.assertNotEqual(book.pk, self.book.pk)
        with self.assertRaises(ValidationError):
            Book.objects.create(
                book_id=book.pk,
                title="Test Title",
                description="Description",
                author="Test Author",
                isbn="1298987954",
                publication_date=date(2000, 1, 1),
                added_by=self.user,
            )

    def test_book_ordering(self):
        """Confirm books are ordered by date_added in descending order."""
        book1 = Book.objects.create(
            title="Test Title",
            description="Test Description",
            author="Test Author",
            isbn="1234565671",
            publication_date=date(2000, 1, 31),
            added_by=self.user,
        )
        book2 = Book.objects.create(
            title="Test Title2",
            description="Test Description 2",
            author="Test Author 2",
            isbn="1234589764",
            publication_date=date.today(),
            added_by=self.user,
        )
        # force dates
        Book.objects.filter(pk=book1.pk).update(
            date_added=timezone.make_aware(datetime(2000, 1, 31, 12, 0, 0))
        )
        Book.objects.filter(pk=book2.pk).update(
            date_added=timezone.make_aware(datetime(2025, 11, 20, 12, 0, 0))
        )
        book1.refresh_from_db()
        book2.refresh_from_db()
        first_book = Book.objects.first()
        last_book = Book.objects.last()
        self.assertEqual(first_book.pk, book2.pk)
        self.assertEqual(last_book.pk, book1.pk)

    def test_book_id_uuid(self):
        """Check that book_id is generated as a UUID."""
        self.assertIsInstance(self.book.book_id, uuid.UUID)

    def test_book_borrow_return_book_functionality(self):
        """
        Verify borrowing reduces copies_available and updates availability status.
        Verify returning increases copies_available and updates availability status.
        """
        self.book.borrow_book()
        self.assertEqual(self.book.copies_available, 0)
        self.assertFalse(self.book.is_available)

        self.book.return_book()
        self.assertEqual(self.book.copies_available, 1)
        self.assertTrue(self.book.is_available)

    def test_is_available_works_fine(self):
        """Confirm is_available property reflects availability correctly."""
        self.assertTrue(self.book.is_available)
        self.book.borrow_book()
        self.assertFalse(self.book.is_available)

    def test_copies_validation(self):
        """Validate business rules:
        1. non-negative counts
        2. available ≤ total
        3. total not reduced below available."""
        book = Book.objects.create(
            title="Validation Test",
            description="desc",
            author="author",
            isbn="1893868797",
            publication_date=date.today(),
            added_by=self.user,
            total_copies=5,
            copies_available=5,
        )
        book.total_copies = -1
        with self.assertRaises(ValidationError):
            book.full_clean()
        book.copies_available = -1
        with self.assertRaises(ValidationError):
            book.full_clean()
        book.total_copies = 3
        book.copies_available = 4
        with self.assertRaises(ValidationError):
            book.full_clean()
        book.total_copies = 2
        with self.assertRaises(ValidationError):
            book.full_clean()

    def test_borrow_boolen_return(self):
        """Borrowing an unavailable book returns False, otherwise True"""
        self.assertTrue(self.book.borrow_book())
        self.assertFalse(self.book.borrow_book())  # attempt to borrow unavailable book.

    def test_get_absolute_url(self):
        """Ensure get_absolute_url returns the correct detail view URL."""
        self.assertEqual(
            self.book.get_absolute_url(),
            reverse("book_detail", kwargs={"pk": self.book.pk}),
        )
