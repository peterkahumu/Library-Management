from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import UserRoles
from books.google_books import GoogleBooksAPIError
from books.models import Book, Genre


User = get_user_model()


class GoogleBooksViewTests(TestCase):
    """Test functionality of Google Books integration views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role=UserRoles.ADMIN,
        )
        self.librarian = User.objects.create_user(
            username="librarian",
            email="librarian@test.com",
            password="librarianpass123",
            role=UserRoles.LIBRARIAN,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="studentpass123",
            role=UserRoles.STUDENT,
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

    def test_search_view_access(self):
        """Anyone can access search page."""
        # Admin access
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("google_books_search"))
        self.assertEqual(response.status_code, 200)

        # Librarian access
        self.client.login(username="librarian", password="librarianpass123")
        response = self.client.get(reverse("google_books_search"))
        self.assertEqual(response.status_code, 200)

        # Student access
        self.client.login(username="student", password="studentpass123")
        response = self.client.get(reverse("google_books_search"))
        self.assertEqual(response.status_code, 200)

    @patch("books.views.GoogleBooksAPI")  # noqa
    def test_search_functionality(self, MockAPI):
        """Test searching for books interacts with API correctly."""
        # Configure mock
        mock_instance = MockAPI.return_value
        mock_instance.search_books.return_value = {
            "total_items": 1,
            "items": [
                {
                    "id": "vol1",
                    "volumeInfo": {
                        "title": "Test Book",
                        "authors": ["Test Author"],
                        "description": "Test Description",
                        "imageLinks": {"thumbnail": "http://test.com/img.jpg"},
                        "publishedDate": "2023-01-01",
                    },
                }
            ],
            "start_index": 0,
            "items_per_page": 20,
        }

        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("google_books_search"), {"q": "test query"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/google_books_search.html")

        # Verify call arguments (views usually pass pagination args too)
        # Based on failure
        mock_instance.search_books.assert_called_with(
            query="test query", start_index=0, max_results=20
        )
        self.assertIn("results", response.context)
        self.assertEqual(len(response.context["results"]), 1)

    @patch("books.views.GoogleBooksAPI")  # noqa
    def test_search_error_handling(self, MockAPI):
        """Test error handling when API fails."""
        mock_instance = MockAPI.return_value
        mock_instance.search_books.side_effect = GoogleBooksAPIError("API Error")

        self.client.login(username="admin", password="adminpass123")
        # Use exact kwargs as view uses
        response = self.client.get(reverse("google_books_search"), {"q": "fail"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API Error")

    @patch("books.views.GoogleBooksAPI")  # noqa
    def test_add_book_view_get(self, MockAPI):
        """Test retrieving book details for adding."""
        mock_instance = MockAPI.return_value
        mock_instance.get_book_details.return_value = {
            "id": "vol1",
            "volumeInfo": {
                "title": "New Book",
                "authors": ["Author"],
                "description": "Desc with <p>tags</p>",
                "industryIdentifiers": [
                    {"type": "ISBN_13", "identifier": "9781234567890"}
                ],
                "publishedDate": "2023",
                "publisher": "Publisher",
                "imageLinks": {"thumbnail": "http://img.url"},
            },
        }

        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(
            reverse("google_books_add", kwargs={"volume_id": "vol1"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_form.html")

        # Verify initial data in form
        form = response.context["form"]
        self.assertEqual(form.initial["title"], "New Book")
        self.assertEqual(form.initial["isbn"], "9781234567890")
        self.assertIn("Desc with", form.initial["description"])

    @patch("books.views.GoogleBooksAPI")  # noqa
    def test_add_book_submit(self, MockAPI):
        """Test submitting the form to add a book from Google Books."""
        self.client.login(username="admin", password="adminpass123")

        # Mock get_book_details for the view's internal logic (form_valid checks cover)
        mock_instance = MockAPI.return_value
        mock_instance.get_book_details.return_value = {
            "id": "vol_ignored",
            "volumeInfo": {
                "title": "Imported Book",
                "imageLinks": {"thumbnail": "http://img.url"},
            },
        }
        mock_instance.extract_cover_url.return_value = None

        data = {
            "title": "Imported Book",
            "description": "Description",
            "isbn": "9780000000001",
            "author": "Imported Author",
            "publication_date": "2023-01-01",
            "total_copies": 5,
            "copies_available": 5,
            "genre": [self.genre.id],
            "language": "en",
            "publisher": "Test Pub",
            "format": "HARDCOPY",
        }

        # Note: The view expects volume_id in URL, but processes POST standard way
        response = self.client.post(
            reverse("google_books_add", kwargs={"volume_id": "vol_ignored"}), data=data
        )

        self.assertEqual(response.status_code, 302)  # Redirects to detail
        self.assertTrue(Book.objects.filter(isbn="9780000000001").exists())
