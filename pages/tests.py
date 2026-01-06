import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from books.models import Book, Genre

User = get_user_model()


class HomeViewTests(TestCase):
    """Test the home page view."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

        # Create some books
        for i in range(3):
            Book.objects.create(
                title=f"Book {i}",
                description="Test",
                isbn=f"123456789012{i}",
                author="Author",
                publication_date=datetime.date(2020, 1, 1),
                total_copies=5,
                copies_available=5,
                added_by=self.user,
            )

        # Create featured books
        for i in range(2):
            book = Book.objects.create(
                title=f"Featured Book {i}",
                description="Test",
                isbn=f"987654321098{i}",
                author="Author",
                publication_date=datetime.date(2020, 1, 1),
                total_copies=5,
                copies_available=5,
                featured=True,
                added_by=self.user,
            )
            book.genre.add(self.genre)

    def test_home_page_loads(self):
        """Home page should load successfully."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")

    def test_home_page_shows_stats(self):
        """Home page should display cached stats."""
        response = self.client.get(reverse("home"))

        self.assertIn("total_books", response.context)
        self.assertIn("total_users", response.context)
        self.assertIn("available_books", response.context)

        # Check values are correct
        self.assertEqual(response.context["total_books"], Book.objects.count())
        self.assertEqual(
            response.context["total_users"], User.objects.filter(is_active=True).count()
        )
        self.assertEqual(
            response.context["available_books"],
            Book.objects.filter(copies_available__gt=0).count(),
        )

    def test_home_page_shows_featured_books(self):
        """Home page should display featured books."""
        response = self.client.get(reverse("home"))

        self.assertIn("featured_books", response.context)
        featured_books = list(response.context["featured_books"])

        # Should have 2 featured books
        self.assertEqual(len(featured_books), 2)

        # All should be featured
        for book in featured_books:
            self.assertTrue(book.featured)

    def test_home_page_accessible_to_anonymous_users(self):
        """Anonymous users should be able to access home page."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
