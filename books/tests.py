import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

import uuid
from datetime import date
from .models import Book, Genre
from .forms import BookForm
from .constants import GENRE_CHOICES

User = get_user_model()


class GenreModelTests(TestCase):
    """Test Genre model behavior."""

    def test_genre_creation(self):
        """Genre should be created with a valid choice."""
        genre, created = Genre.objects.get_or_create(name="FANTASY")
        self.assertEqual(genre.name, "FANTASY")
        self.assertIn(genre.name, [choice[0] for choice in GENRE_CHOICES])

    def test_genre_string_representation(self):
        """Genre __str__ should return human-readable name."""
        genre, created = Genre.objects.get_or_create(name="SCIFI")
        self.assertEqual(str(genre), "Science Fiction")

    def test_genre_unique_constraint(self):
        """Genre names should be unique."""
        Genre.objects.get_or_create(name="MYSTERY")
        with self.assertRaises(Exception):  # IntegrityError
            # Force creation without get_or_create
            Genre.objects.create(name="MYSTERY")

    def test_genre_ordering(self):
        """Genres should be ordered by name."""
        Genre.objects.get_or_create(name="ROMANCE")
        Genre.objects.get_or_create(name="FANTASY")
        Genre.objects.get_or_create(name="ADVENTURE")
        genres = list(
            Genre.objects.filter(name__in=["ROMANCE", "FANTASY", "ADVENTURE"]).order_by(
                "name"
            )
        )
        self.assertEqual([g.name for g in genres], ["ADVENTURE", "FANTASY", "ROMANCE"])


class BookModelTests(TestCase):
    """Test Book model behavior and business logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="student",
        )
        self.genre_fantasy, _ = Genre.objects.get_or_create(name="FANTASY")
        self.genre_scifi, _ = Genre.objects.get_or_create(name="SCIFI")

    def create_book(self, **kwargs):
        """Helper to create a book with defaults."""
        defaults = {
            "title": "Test Book",
            "description": "A test book description",
            "isbn": "1234567890123",
            "author": "Test Author",
            "publication_date": datetime.date(2020, 1, 1),
            "language": "en",
            "total_copies": 5,
            "copies_available": 5,
            "added_by": self.user,
        }
        defaults.update(kwargs)
        book = Book.objects.create(**defaults)
        if "genre" not in kwargs:
            book.genre.add(self.genre_fantasy)
        return book

    def test_book_creation(self):
        """Book should be created with required fields."""
        book = self.create_book()
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.copies_available, 5)
        self.assertTrue(book.is_available)

    def test_book_uuid_primary_key(self):
        """Book should use UUID as primary key."""
        book = self.create_book()
        self.assertIsNotNone(book.book_id)
        self.assertIsInstance(book.book_id, uuid.UUID)
        # UUID should be auto-generated and unique
        book2 = self.create_book(isbn="9876543210987")
        self.assertNotEqual(book.book_id, book2.book_id)

    def test_book_string_representation(self):
        """Book __str__ should return title."""
        book = self.create_book(title="The Hobbit")
        self.assertEqual(str(book), "The Hobbit")

    def test_book_is_available_property(self):
        """is_available should be True when copies_available > 0."""
        book = self.create_book(copies_available=3)
        self.assertTrue(book.is_available)

        book.copies_available = 0
        book.save()
        self.assertFalse(book.is_available)

    def test_book_borrow_success(self):
        """Borrowing should decrease available copies."""
        book = self.create_book(copies_available=3)
        result = book.borrow_book()
        self.assertTrue(result)
        book.refresh_from_db()
        self.assertEqual(book.copies_available, 2)

    def test_book_borrow_when_unavailable(self):
        """Borrowing should fail when no copies available."""
        book = self.create_book(copies_available=0)
        result = book.borrow_book()
        self.assertFalse(result)
        book.refresh_from_db()
        self.assertEqual(book.copies_available, 0)

    def test_book_return_success(self):
        """Returning should increase available copies."""
        book = self.create_book(total_copies=5, copies_available=2)
        result = book.return_book()
        self.assertTrue(result)
        book.refresh_from_db()
        self.assertEqual(book.copies_available, 3)

    def test_book_return_when_at_capacity(self):
        """Returning should fail when all copies already available."""
        book = self.create_book(total_copies=5, copies_available=5)
        result = book.return_book()
        self.assertFalse(result)
        book.refresh_from_db()
        self.assertEqual(book.copies_available, 5)

    def test_book_get_absolute_url(self):
        """get_absolute_url should return correct detail URL."""
        book = self.create_book()
        expected_url = reverse("book_detail", kwargs={"pk": book.book_id})
        self.assertEqual(book.get_absolute_url(), expected_url)

    def test_book_validation_negative_total_copies(self):
        """Book should not allow negative total_copies."""
        book = self.create_book()
        book.total_copies = -1
        with self.assertRaises(ValidationError) as context:
            book.save()
        self.assertIn("total_copies", context.exception.message_dict)

    def test_book_validation_negative_copies_available(self):
        """Book should not allow negative copies_available."""
        book = self.create_book()
        book.copies_available = -1
        with self.assertRaises(ValidationError) as context:
            book.save()
        self.assertIn("copies_available", context.exception.message_dict)

    def test_book_validation_available_exceeds_total(self):
        """copies_available should not exceed total_copies."""
        # Create book first, then try to violate constraint
        book = self.create_book(total_copies=5, copies_available=5)
        book.copies_available = 10
        with self.assertRaises(ValidationError) as context:
            book.save()
        self.assertIn("copies_available", context.exception.message_dict)

    def test_book_validation_reduce_total_below_available(self):
        """Cannot reduce total_copies below current copies_available."""
        book = self.create_book(total_copies=10, copies_available=8)
        book.total_copies = 5  # Try to set below available (8)
        with self.assertRaises(ValidationError) as context:
            book.save()

        self.assertTrue(
            "total_copies" in context.exception.message_dict
            or "copies_available" in context.exception.message_dict
        )

    def test_book_many_to_many_genres(self):
        """Book can have multiple genres."""
        book = self.create_book()
        book.genre.add(self.genre_scifi)
        self.assertEqual(book.genre.count(), 2)
        self.assertIn(self.genre_fantasy, book.genre.all())
        self.assertIn(self.genre_scifi, book.genre.all())

    def test_book_default_language(self):
        """Book should default to English language."""
        book = self.create_book()
        self.assertEqual(book.language, "en")

    def test_book_ordering(self):
        """Books should be ordered by date_added descending (newest first)."""
        book1 = self.create_book(title="Old Book", isbn="1111111111111")
        book2 = self.create_book(title="New Book", isbn="2222222222222")
        books = list(Book.objects.all())
        self.assertEqual(books[0], book2)
        self.assertEqual(books[1], book1)

    def test_book_unique_isbn(self):
        """ISBN should be unique across all books."""
        self.create_book(isbn="1234567890123")
        with self.assertRaises(ValidationError):
            self.create_book(isbn="1234567890123")

    def test_book_mandatory_fields(self):
        """Missing mandatory fields should raise validation errors."""
        book = Book()
        with self.assertRaises(ValidationError) as cm:
            book.full_clean()
        errors = cm.exception.message_dict
        self.assertIn("title", errors)
        self.assertIn("description", errors)
        self.assertIn("isbn", errors)
        self.assertIn("author", errors)
        self.assertIn("publication_date", errors)
        self.assertIn("added_by", errors)

    def test_book_default_copies(self):
        """Books should default to 1 total copy and 1 available."""
        self.create_book()
        # Reset to test defaults
        book2 = Book.objects.create(
            title="Default Test",
            description="Test",
            isbn="9999999999999",
            author="Author",
            publication_date=date(2020, 1, 1),
            added_by=self.user,
        )
        self.assertEqual(book2.total_copies, 1)
        self.assertEqual(book2.copies_available, 1)


class BookFormTests(TestCase):
    """Test BookForm validation and behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.genre_fantasy, _ = Genre.objects.get_or_create(name="FANTASY")
        self.genre_scifi, _ = Genre.objects.get_or_create(name="SCIFI")

    def get_valid_form_data(self, **kwargs):
        """Helper to get valid form data."""
        data = {
            "title": "Test Book",
            "description": "A test description",
            "isbn": "1234567890123",
            "author": "Test Author",
            "publication_date": "2020-01-01",
            "language": "en",
            "total_copies": 5,
            "copies_available": 5,
            "genre": [self.genre_fantasy.id],
        }
        data.update(kwargs)
        return data

    def test_form_valid_with_required_fields(self):
        """Form should be valid with all required fields."""
        form = BookForm(data=self.get_valid_form_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_isbn_not_numeric(self):
        """ISBN must be numeric."""
        data = self.get_valid_form_data(isbn="ABC1234567890")
        form = BookForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("isbn", form.errors)

    def test_form_invalid_isbn_wrong_length(self):
        """ISBN must be 10 or 13 digits."""
        # Too short
        data = self.get_valid_form_data(isbn="12345")
        form = BookForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("isbn", form.errors)

        # Too long
        data = self.get_valid_form_data(isbn="12345678901234567890")
        form = BookForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("isbn", form.errors)

    def test_form_valid_isbn_10_digits(self):
        """ISBN with 10 digits should be valid."""
        data = self.get_valid_form_data(isbn="1234567890")
        form = BookForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_valid_isbn_13_digits(self):
        """ISBN with 13 digits should be valid."""
        data = self.get_valid_form_data(isbn="1234567890123")
        form = BookForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_future_publication_date(self):
        """Publication date cannot be in the future."""
        future_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        data = self.get_valid_form_data(publication_date=future_date)
        form = BookForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("publication_date", form.errors)

    def test_form_valid_publication_date_today(self):
        """Publication date can be today."""
        data = self.get_valid_form_data(
            publication_date=datetime.date.today().isoformat()
        )
        form = BookForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_no_genre(self):
        """Book must have at least one genre."""
        data = self.get_valid_form_data(genre=[])
        form = BookForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("genre", form.errors)

    def test_form_valid_multiple_genres(self):
        """Book can have multiple genres."""
        data = self.get_valid_form_data(
            genre=[self.genre_fantasy.id, self.genre_scifi.id]
        )
        form = BookForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)


class BookListViewTests(TestCase):
    """Test BookListView functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre_fantasy, _ = Genre.objects.get_or_create(name="FANTASY")
        self.genre_scifi, _ = Genre.objects.get_or_create(name="SCIFI")
        self.genre_mystery, _ = Genre.objects.get_or_create(name="MYSTERY")

        # Create test books
        self.book1 = Book.objects.create(
            title="Fantasy Book",
            description="A fantasy book",
            isbn="1111111111111",
            author="Author One",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        self.book1.genre.add(self.genre_fantasy)

        self.book2 = Book.objects.create(
            title="Sci-Fi Book",
            description="A sci-fi book",
            isbn="2222222222222",
            author="Author Two",
            publication_date=datetime.date(2021, 1, 1),
            total_copies=3,
            copies_available=3,
            added_by=self.user,
        )
        self.book2.genre.add(self.genre_scifi)

    def test_book_list_view_status_code(self):
        """Book list view should return 200."""
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 200)

    def test_book_list_view_uses_correct_template(self):
        """Book list view should use correct template."""
        response = self.client.get(reverse("book_list"))
        self.assertTemplateUsed(response, "books/book_list.html")

    def test_book_list_view_shows_all_books(self):
        """Book list view should display all books."""
        response = self.client.get(reverse("book_list"))
        self.assertEqual(len(response.context["books"]), 2)
        self.assertIn(self.book1, response.context["books"])
        self.assertIn(self.book2, response.context["books"])

    def test_book_list_view_filter_by_genre(self):
        """Book list view should filter by genre."""
        response = self.client.get(reverse("book_list") + "?genre=FANTASY")
        self.assertEqual(len(response.context["books"]), 1)
        self.assertIn(self.book1, response.context["books"])
        self.assertNotIn(self.book2, response.context["books"])

    def test_book_list_view_search_by_title(self):
        """Book list view should search by title."""
        response = self.client.get(reverse("book_list") + "?query=Fantasy")
        self.assertEqual(len(response.context["books"]), 1)
        self.assertIn(self.book1, response.context["books"])

    def test_book_list_view_search_by_author(self):
        """Book list view should search by author."""
        response = self.client.get(reverse("book_list") + "?query=Author Two")
        self.assertEqual(len(response.context["books"]), 1)
        self.assertIn(self.book2, response.context["books"])

    def test_book_list_view_search_by_isbn(self):
        """Book list view should search by ISBN."""
        response = self.client.get(reverse("book_list") + "?query=1111111111111")
        self.assertEqual(len(response.context["books"]), 1)
        self.assertIn(self.book1, response.context["books"])

    def test_book_list_view_pagination(self):
        """Book list view should paginate results."""
        # Create more books to trigger pagination (paginate_by=8)
        for i in range(10):
            book = Book.objects.create(
                title=f"Book {i}",
                description="Description",
                isbn=f"300000000000{i}",
                author="Author",
                publication_date=datetime.date(2020, 1, 1),
                total_copies=1,
                copies_available=1,
                added_by=self.user,
            )
            book.genre.add(self.genre_fantasy)

        response = self.client.get(reverse("book_list"))
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["books"]), 8)

    def test_book_list_view_context_contains_genres(self):
        """Book list view should include all genres in context."""
        response = self.client.get(reverse("book_list"))
        self.assertIn("all_genres", response.context)
        # Should contain at least the genres we created
        self.assertGreaterEqual(response.context["all_genres"].count(), 3)
        # Verify our specific genres are included
        genre_names = [g.name for g in response.context["all_genres"]]
        self.assertIn("FANTASY", genre_names)
        self.assertIn("SCIFI", genre_names)
        self.assertIn("MYSTERY", genre_names)

    def test_book_list_view_filter_by_genre_all(self):
        """Book list with genre='all' should show all books."""
        response = self.client.get(reverse("book_list") + "?genre=all")
        self.assertEqual(len(response.context["books"]), 2)


class BookDetailViewTests(TestCase):
    """Test BookDetailView functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre_fantasy, _ = Genre.objects.get_or_create(name="FANTASY")
        self.genre_scifi, _ = Genre.objects.get_or_create(name="SCIFI")

        self.book = Book.objects.create(
            title="Test Book",
            description="Test description",
            isbn="1234567890123",
            author="Test Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=3,
            added_by=self.user,
        )
        self.book.genre.add(self.genre_fantasy, self.genre_scifi)

    def test_book_detail_view_status_code(self):
        """Book detail view should return 200."""
        response = self.client.get(
            reverse("book_detail", kwargs={"pk": self.book.book_id})
        )
        self.assertEqual(response.status_code, 200)

    def test_book_detail_view_uses_correct_template(self):
        """Book detail view should use correct template."""
        response = self.client.get(
            reverse("book_detail", kwargs={"pk": self.book.book_id})
        )
        self.assertTemplateUsed(response, "books/book_detail.html")

    def test_book_detail_view_shows_correct_book(self):
        """Book detail view should display correct book."""
        response = self.client.get(
            reverse("book_detail", kwargs={"pk": self.book.book_id})
        )
        self.assertEqual(response.context["book"], self.book)

    def test_book_detail_view_shows_genres(self):
        """Book detail view should show book genres."""
        response = self.client.get(
            reverse("book_detail", kwargs={"pk": self.book.book_id})
        )
        self.assertIn("genres", response.context)
        self.assertEqual(len(response.context["genres"]), 2)
        self.assertIn("FANTASY", response.context["genres"])
        self.assertIn("SCIFI", response.context["genres"])

    def test_book_detail_view_shows_related_books(self):
        """Book detail view should show related books by genre."""
        # Create related book with same genre
        related_book = Book.objects.create(
            title="Related Book",
            description="Related description",
            isbn="9999999999999",
            author="Related Author",
            publication_date=datetime.date(2021, 1, 1),
            total_copies=2,
            copies_available=2,
            added_by=self.user,
        )
        related_book.genre.add(self.genre_fantasy)

        response = self.client.get(
            reverse("book_detail", kwargs={"pk": self.book.book_id})
        )
        self.assertIn("related_books", response.context)
        self.assertIn(related_book, response.context["related_books"])
        self.assertNotIn(self.book, response.context["related_books"])

    def test_book_detail_view_nonexistent_book(self):
        """Book detail view should return 404 for nonexistent book."""
        fake_uuid = uuid.uuid4()
        response = self.client.get(reverse("book_detail", kwargs={"pk": fake_uuid}))
        self.assertEqual(response.status_code, 404)

    def test_book_detail_view_no_related_books(self):
        """Book detail view should handle books with no related books."""
        unique_genre, _ = Genre.objects.get_or_create(name="HORROR")
        solo_book = Book.objects.create(
            title="Solo Book",
            description="No related books",
            isbn="8888888888888",
            author="Solo Author",
            publication_date=datetime.date(2022, 1, 1),
            total_copies=1,
            copies_available=1,
            added_by=self.user,
        )
        solo_book.genre.add(unique_genre)

        response = self.client.get(
            reverse("book_detail", kwargs={"pk": solo_book.book_id})
        )
        self.assertEqual(len(response.context["related_books"]), 0)


class BookCreateViewTests(TestCase):
    """Test BookCreateView functionality and permissions."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            role="admin",
        )
        self.librarian = User.objects.create_user(
            username="librarian",
            email="librarian@example.com",
            password="libpass123",
            role="librarian",
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="studentpass123",
            role="student",
        )
        self.genre_fantasy, _ = Genre.objects.get_or_create(name="FANTASY")

    def test_book_create_view_requires_login(self):
        """Book create view should require login."""
        response = self.client.get(reverse("book_create"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response.url.startswith("/accounts/login"))

    def test_book_create_view_admin_access(self):
        """Admin should be able to access book create view."""
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("book_create"))
        self.assertEqual(response.status_code, 200)

    def test_book_create_view_librarian_access(self):
        """Librarian should be able to access book create view."""
        self.client.login(username="librarian", password="libpass123")
        response = self.client.get(reverse("book_create"))
        self.assertEqual(response.status_code, 200)

    def test_book_create_view_student_denied(self):
        """Student should not be able to access book create view."""
        self.client.login(username="student", password="studentpass123")
        response = self.client.get(reverse("book_create"))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_book_create_view_uses_correct_template(self):
        """Book create view should use correct template."""
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("book_create"))
        self.assertTemplateUsed(response, "books/book_create.html")

    def test_book_create_view_creates_book(self):
        """Book create view should create a new book."""
        self.client.login(username="admin", password="adminpass123")
        data = {
            "title": "New Book",
            "description": "A new book",
            "isbn": "1234567890123",
            "author": "New Author",
            "publication_date": "2020-01-01",
            "language": "en",
            "total_copies": 5,
            "copies_available": 5,
            "genre": [self.genre_fantasy.id],
        }
        self.client.post(reverse("book_create"), data=data)
        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.first()
        self.assertEqual(book.title, "New Book")
        self.assertEqual(book.added_by, self.admin)

    def test_book_create_view_sets_added_by(self):
        """Book create should set added_by to current user."""
        self.client.login(username="librarian", password="libpass123")
        data = {
            "title": "Librarian Book",
            "description": "Book by librarian",
            "isbn": "9999999999999",
            "author": "Author",
            "publication_date": "2020-01-01",
            "language": "en",
            "total_copies": 3,
            "copies_available": 3,
            "genre": [self.genre_fantasy.id],
        }
        self.client.post(reverse("book_create"), data=data)
        book = Book.objects.first()
        self.assertEqual(book.added_by, self.librarian)

    def test_book_create_view_redirects_to_detail(self):
        """Book create should redirect to book detail on success."""
        self.client.login(username="admin", password="adminpass123")
        data = {
            "title": "Redirect Test",
            "description": "Test redirect",
            "isbn": "1111111111111",
            "author": "Author",
            "publication_date": "2020-01-01",
            "language": "en",
            "total_copies": 1,
            "copies_available": 1,
            "genre": [self.genre_fantasy.id],
        }
        response = self.client.post(reverse("book_create"), data=data, follow=True)
        book = Book.objects.first()
        self.assertRedirects(
            response, reverse("book_detail", kwargs={"pk": book.book_id})
        )


class BookEditViewTests(TestCase):
    """Test BookEditView functionality and permissions."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            role="admin",
        )
        self.librarian = User.objects.create_user(
            username="librarian",
            email="librarian@example.com",
            password="libpass123",
            role="librarian",
        )
        self.student_owner = User.objects.create_user(
            username="student_owner",
            email="owner@example.com",
            password="ownerpass123",
            role="student",
        )
        self.student_other = User.objects.create_user(
            username="student_other",
            email="other@example.com",
            password="otherpass123",
            role="student",
        )
        self.genre_fantasy, _ = Genre.objects.get_or_create(name="FANTASY")

        self.book = Book.objects.create(
            title="Test Book",
            description="Test description",
            isbn="1234567890123",
            author="Test Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.student_owner,
        )
        self.book.genre.add(self.genre_fantasy)

    def test_book_edit_view_requires_login(self):
        """Book edit view should require login."""
        response = self.client.get(
            reverse("book_edit", kwargs={"pk": self.book.book_id})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_book_edit_view_admin_access(self):
        """Admin should be able to edit any book."""
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(
            reverse("book_edit", kwargs={"pk": self.book.book_id})
        )
        self.assertEqual(response.status_code, 200)

    def test_book_edit_view_librarian_access(self):
        """Librarian should be able to edit any book."""
        self.client.login(username="librarian", password="libpass123")
        response = self.client.get(
            reverse("book_edit", kwargs={"pk": self.book.book_id})
        )
        self.assertEqual(response.status_code, 200)

    def test_book_edit_view_owner_access(self):
        """Book owner should be able to edit their own book."""
        self.client.login(username="student_owner", password="ownerpass123")
        response = self.client.get(
            reverse("book_edit", kwargs={"pk": self.book.book_id})
        )
        self.assertEqual(response.status_code, 200)

    def test_book_edit_view_non_owner_denied(self):
        """Non-owner student should not be able to edit book."""
        self.client.login(username="student_other", password="otherpass123")
        response = self.client.get(
            reverse("book_edit", kwargs={"pk": self.book.book_id})
        )
        self.assertEqual(response.status_code, 403)

    def test_book_edit_view_uses_correct_template(self):
        """Book edit view should use correct template."""
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(
            reverse("book_edit", kwargs={"pk": self.book.book_id})
        )
        self.assertTemplateUsed(response, "books/book_edit.html")

    def test_book_edit_view_updates_book(self):
        """Book edit view should update book data."""
        self.client.login(username="admin", password="adminpass123")
        data = {
            "title": "Updated Title",
            "description": "Updated description",
            "isbn": "1234567890123",
            "author": "Updated Author",
            "publication_date": "2020-01-01",
            "language": "fr",
            "total_copies": 10,
            "copies_available": 8,
            "genre": [self.genre_fantasy.id],
        }
        self.client.post(
            reverse("book_edit", kwargs={"pk": self.book.book_id}), data=data
        )
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Updated Title")
        self.assertEqual(self.book.language, "fr")
        self.assertEqual(self.book.total_copies, 10)

    def test_book_edit_view_preserves_added_by(self):
        """Book edit should not change the added_by field."""
        self.client.login(username="admin", password="adminpass123")
        original_user = self.book.added_by
        data = {
            "title": "Updated Title",
            "description": "Updated description",
            "isbn": "1234567890123",
            "author": "Updated Author",
            "publication_date": "2020-01-01",
            "language": "en",
            "total_copies": 5,
            "copies_available": 5,
            "genre": [self.genre_fantasy.id],
        }
        self.client.post(
            reverse("book_edit", kwargs={"pk": self.book.book_id}), data=data
        )
        self.book.refresh_from_db()
        self.assertEqual(self.book.added_by, original_user)


class GenresContextProcessorTests(TestCase):
    """Test genres_context custom context processor."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

        # Create genres with different book counts
        self.genre1, _ = Genre.objects.get_or_create(name="FANTASY")
        self.genre2, _ = Genre.objects.get_or_create(name="SCIFI")
        self.genre3, _ = Genre.objects.get_or_create(name="MYSTERY")
        self.genre4, _ = Genre.objects.get_or_create(name="ROMANCE")
        self.genre5, _ = Genre.objects.get_or_create(name="HORROR")
        self.genre6, _ = Genre.objects.get_or_create(name="THRILLER")

        # Create books in different genres
        for i in range(10):  # 10 books in FANTASY
            book = Book.objects.create(
                title=f"Fantasy {i}",
                description="Description",
                isbn=f"111111111111{i}",
                author="Author",
                publication_date=datetime.date(2020, 1, 1),
                total_copies=1,
                copies_available=1,
                added_by=self.user,
            )
            book.genre.add(self.genre1)

        for i in range(5):  # 5 books in SCIFI
            book = Book.objects.create(
                title=f"SciFi {i}",
                description="Description",
                isbn=f"222222222222{i}",
                author="Author",
                publication_date=datetime.date(2020, 1, 1),
                total_copies=1,
                copies_available=1,
                added_by=self.user,
            )
            book.genre.add(self.genre2)

    def test_genres_context_returns_top_five(self):
        """Context processor should return top 5 genres by book count."""
        from .views import genres_context

        request = self.client.get(reverse("book_list")).wsgi_request
        context = genres_context(request)
        self.assertIn("genres", context)
        self.assertEqual(len(context["genres"]), 5)

    def test_genres_context_ordered_by_book_count(self):
        """Genres should be ordered by book count descending."""
        from .views import genres_context

        request = self.client.get(reverse("book_list")).wsgi_request
        context = genres_context(request)
        genres = list(context["genres"])
        # FANTASY should be first (10 books), SCIFI second (5 books)
        self.assertEqual(genres[0], self.genre1)
        self.assertEqual(genres[1], self.genre2)
