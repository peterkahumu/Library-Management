import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model

from books.models import Book, Genre
from .utils import get_cached_stats

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


class GetCachedStatsTests(TestCase):
    """Test the get_cached_stats utility function."""

    def setUp(self):
        """Clear cache and create test fixtures."""
        cache.clear()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

    def test_get_cached_stats_returns_correct_data(self):
        """get_cached_stats should return correct statistics."""
        # Create test data
        for i in range(5):
            Book.objects.create(
                title=f"Book {i}",
                description="Test",
                isbn=f"123456789012{i}",
                author="Author",
                publication_date=datetime.date(2020, 1, 1),
                total_copies=5,
                copies_available=3,
                added_by=self.user,
            )

        User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass",
        )

        stats = get_cached_stats()

        self.assertEqual(stats["total_books"], 5)
        self.assertEqual(stats["total_users"], 2)  # 2 active users
        self.assertEqual(stats["available_books"], 5)  # All books have available copies

    def test_get_cached_stats_caches_results(self):
        """get_cached_stats should cache results in Redis."""
        # First call - should query DB and cache
        stats = get_cached_stats()

        # Check cache was set
        self.assertIsNotNone(cache.get("stats:total_books"))
        self.assertIsNotNone(cache.get("stats:total_users"))
        self.assertIsNotNone(cache.get("stats:available_books"))

        # Values should match
        self.assertEqual(cache.get("stats:total_books"), stats["total_books"])
        self.assertEqual(cache.get("stats:total_users"), stats["total_users"])
        self.assertEqual(cache.get("stats:available_books"), stats["available_books"])

    def test_get_cached_stats_uses_cache_on_second_call(self):
        """Second call to get_cached_stats should use cached data."""
        # First call
        stats1 = get_cached_stats()

        # Create new book (should not affect cached stats)
        Book.objects.create(
            title="New Book",
            description="Test",
            isbn="9999999999999",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=1,
            copies_available=1,
            added_by=self.user,
        )

        # Clear the cache to simulate it being invalidated by signal
        # Then set it again to test cache retrieval
        cache.set("stats:total_books", stats1["total_books"], timeout=60)
        cache.set("stats:total_users", stats1["total_users"], timeout=60)
        cache.set("stats:available_books", stats1["total_users"], timeout=60)

        # Second call - should use cache (old value)
        stats2 = get_cached_stats()

        # Should return cached value (not the new count)
        self.assertEqual(stats2["total_books"], stats1["total_books"])

    def test_get_cached_stats_handles_zero_books(self):
        """get_cached_stats should handle zero books gracefully."""
        stats = get_cached_stats()

        self.assertEqual(stats["total_books"], 0)
        self.assertEqual(stats["available_books"], 0)

    def test_get_cached_stats_counts_only_active_users(self):
        """get_cached_stats should only count active users."""
        # Create active and inactive users
        User.objects.create_user(
            username="active_user",
            email="active@example.com",
            password="pass",
            is_active=True,
        )

        User.objects.create_user(
            username="inactive_user",
            email="inactive@example.com",
            password="pass",
            is_active=False,
        )

        stats = get_cached_stats()

        # Should count 2 active users (testuser from setUp + active_user)
        # Should NOT count inactive_user
        self.assertEqual(stats["total_users"], 2)

    def test_get_cached_stats_counts_only_available_books(self):
        """get_cached_stats should only count books with available copies."""
        # Create books with and without available copies
        Book.objects.create(
            title="Available Book",
            description="Test",
            isbn="1111111111111",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=3,
            added_by=self.user,
        )

        Book.objects.create(
            title="Unavailable Book",
            description="Test",
            isbn="2222222222222",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=0,  # No copies available
            added_by=self.user,
        )

        stats = get_cached_stats()

        # Should count 2 total books but only 1 available
        self.assertEqual(stats["total_books"], 2)
        self.assertEqual(stats["available_books"], 1)


class PagesCacheIntegrationTests(TestCase):
    """Test cache integration with signals in pages app."""

    def setUp(self):
        """Clear cache and create test fixtures."""
        cache.clear()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

    def test_creating_book_invalidates_home_page_cache(self):
        """Creating a book should invalidate relevant cache keys."""
        # Get initial stats (caches them)
        stats1 = get_cached_stats()
        initial_books = stats1["total_books"]

        # Verify cache is set
        self.assertIsNotNone(cache.get("stats:total_books"))

        # Create a new book (signal should invalidate cache)
        Book.objects.create(
            title="New Book",
            description="Test",
            isbn="1234567890123",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )

        # Cache should be invalidated
        self.assertIsNone(cache.get("stats:total_books"))

        # Getting stats again should fetch fresh data
        stats2 = get_cached_stats()
        self.assertEqual(stats2["total_books"], initial_books + 1)

    def test_creating_user_invalidates_home_page_cache(self):
        """Creating a user should invalidate user stats cache."""
        # Get initial stats
        stats1 = get_cached_stats()
        initial_users = stats1["total_users"]

        # Verify cache is set
        self.assertIsNotNone(cache.get("stats:total_users"))

        # Create a new user (signal should invalidate cache)
        User.objects.create_user(
            username="newuser",
            email="new@example.com",
            password="pass",
        )

        # Cache should be invalidated
        self.assertIsNone(cache.get("stats:total_users"))

        # Getting stats again should fetch fresh data
        stats2 = get_cached_stats()
        self.assertEqual(stats2["total_users"], initial_users + 1)
