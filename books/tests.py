from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from datetime import date
from .models import Book, Genre

# # Create your tests here.


class BookModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        book = self.book

        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.description, "Test Book description")
        self.assertEqual(book.author, "Test Author")
        self.assertEqual(book.publication_date, date(year=2000, month=1, day=31))
        self.assertEqual(book.added_by, self.user)
        self.assertEqual(book.language, "en")
        self.assertEqual(book.isbn, "1234567890")
        self.assertIn(self.genre, book.genre.all())
        self.assertIn(self.genre1, book.genre.all())

    def test_mandatory_fields(self):
        book = Book()

        with self.assertRaises(ValidationError) as cm:
            book.full_clean()

        errors = cm.exception.message_dict
        self.assertIn("title", errors)
        self.assertIn("description", errors)
        self.assertIn("isbn", errors)
        self.assertIn("author", errors)
        self.assertIn("publication_date", errors)
        self.assertIn("genre", errors)

    def test_default_fields(self):
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
        book = Book(
            title="Test book",
            description="Test description",
            isbn=1234567890,
            author="Test author",
            publication_date=date(2000, 1, 31),
            added_by=self.user,
        )

        book.genre.set([self.genre1])

        with self.assertRaises(ValidationError) as cm:
            book.full_clean()

        errors = cm.exception.message_dict
        self.assertIn("isbn", errors)
