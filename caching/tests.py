import datetime
from datetime import timedelta
from django.test import TestCase
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone

from books.models import Book, Genre
from book_circulation.models import Transaction
from caching.services import LibraryCacheService

User = get_user_model()


class UserCacheInvalidationTests(TestCase):
    """Test cache invalidation signals for user stats."""

    def setUp(self):
        """Clear cache before each test."""
        from django.core.cache import cache

        cache.clear()

    def test_cache_invalidated_on_user_creation(self):
        """Creating a user should clear stats:total_users cache."""
        from django.core.cache import cache

        cache.set("stats:total_users", 100)
        self.assertEqual(cache.get("stats:total_users"), 100)

        User.objects.create_user(
            username="newuser",
            email="new@example.com",
            password="testpass123",
            first_name="New",
            last_name="User",
        )

        self.assertIsNone(cache.get("stats:total_users"))

    def test_cache_invalidated_on_user_update(self):
        """Updating a user should clear stats:total_users cache."""
        from django.core.cache import cache

        user = User.objects.create_user(
            username="updateuser",
            email="update@example.com",
            password="testpass123",
            first_name="Update",
            last_name="User",
        )

        cache.set("stats:total_users", 100)
        self.assertEqual(cache.get("stats:total_users"), 100)

        user.first_name = "Updated"
        user.save()

        self.assertIsNone(cache.get("stats:total_users"))

    def test_cache_invalidated_on_user_deletion(self):
        """Deleting a user should clear stats:total_users cache."""
        from django.core.cache import cache

        user = User.objects.create_user(
            username="deleteuser",
            email="delete@example.com",
            password="testpass123",
            first_name="Delete",
            last_name="User",
        )

        cache.set("stats:total_users", 100)
        self.assertEqual(cache.get("stats:total_users"), 100)

        user.delete()

        self.assertIsNone(cache.get("stats:total_users"))

    def test_cache_not_affected_by_other_operations(self):
        """Cache should only be invalidated by user save/delete, not reads."""
        from django.core.cache import cache

        User.objects.create_user(
            username="readuser", email="read@example.com", password="testpass123"
        )

        cache.set("stats:total_users", 100)

        # Reading user shouldn't invalidate cache
        User.objects.get(username="readuser")
        self.assertEqual(cache.get("stats:total_users"), 100)

        # Filtering shouldn't invalidate cache
        User.objects.filter(is_active=True)
        self.assertEqual(cache.get("stats:total_users"), 100)


class BookCacheInvalidationTests(TestCase):
    """Test cache invalidation signals for book stats."""

    def setUp(self):
        """Clear cache and create test fixtures."""
        from django.core.cache import cache

        cache.clear()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

    def test_cache_invalidated_on_book_creation(self):
        """Creating a book should clear book-related cache."""
        from django.core.cache import cache

        cache.set("stats:total_books", 100)
        cache.set("stats:available_books", 50)
        self.assertEqual(cache.get("stats:total_books"), 100)
        self.assertEqual(cache.get("stats:available_books"), 50)

        book = Book.objects.create(
            title="New Book",
            description="Test",
            isbn="1234567890123",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        book.genre.add(self.genre)

        self.assertIsNone(cache.get("stats:total_books"))
        self.assertIsNone(cache.get("stats:available_books"))

    def test_cache_invalidated_on_book_update(self):
        """Updating a book should clear book-related cache."""
        from django.core.cache import cache

        book = Book.objects.create(
            title="Update Book",
            description="Test",
            isbn="1234567890123",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        book.genre.add(self.genre)

        cache.set("stats:total_books", 100)
        cache.set("stats:available_books", 50)
        self.assertEqual(cache.get("stats:total_books"), 100)
        self.assertEqual(cache.get("stats:available_books"), 50)

        book.title = "Updated Title"
        book.save()

        self.assertIsNone(cache.get("stats:total_books"))
        self.assertIsNone(cache.get("stats:available_books"))

    def test_cache_invalidated_on_book_deletion(self):
        """Deleting a book should clear book-related cache."""
        from django.core.cache import cache

        book = Book.objects.create(
            title="Delete Book",
            description="Test",
            isbn="1234567890123",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        book.genre.add(self.genre)

        cache.set("stats:total_books", 100)
        cache.set("stats:available_books", 50)
        self.assertEqual(cache.get("stats:total_books"), 100)
        self.assertEqual(cache.get("stats:available_books"), 50)

        book.delete()

        self.assertIsNone(cache.get("stats:total_books"))
        self.assertIsNone(cache.get("stats:available_books"))

    def test_cache_invalidated_on_availability_change(self):
        """Changing book availability should clear available_books cache."""
        from django.core.cache import cache

        book = Book.objects.create(
            title="Borrow Book",
            description="Test",
            isbn="1234567890123",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        book.genre.add(self.genre)

        cache.set("stats:available_books", 50)
        self.assertEqual(cache.get("stats:available_books"), 50)

        # Borrow a book (changes copies_available)
        book.borrow_book()

        self.assertIsNone(cache.get("stats:available_books"))

    def test_user_cache_not_affected_by_book_changes(self):
        """Book changes should not affect user cache."""
        from django.core.cache import cache

        cache.set("stats:total_users", 200)

        book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        book.genre.add(self.genre)

        # User cache should remain intact
        self.assertEqual(cache.get("stats:total_users"), 200)


class TransactionCacheInvalidationTests(TestCase):
    """Test cache invalidation when transactions change."""

    def setUp(self):
        """Create test fixtures and clear cache."""
        cache.clear()

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

    def test_cache_invalidated_on_transaction_creation(self):
        """
        Creating a transaction with ISSUED status should clear availability cache.
        """
        cache.set("stats:available_books", 100)
        cache.set("stats:total_books", 200)

        Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        self.assertIsNone(cache.get("stats:available_books"))
        # None because transaction -> book update -> invalidates total books
        self.assertIsNone(cache.get("stats:total_books"))

    def test_cache_invalidated_on_transaction_return(self):
        """
        Returning a transaction should clear availability cache.
        """
        transaction = Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="ISSUED",
        )

        cache.set("stats:available_books", 100)
        cache.set("stats:total_books", 200)

        # Verify cache set
        self.assertEqual(cache.get("stats:available_books"), 100)

        transaction.mark_as_returned()

        self.assertIsNone(cache.get("stats:available_books"))
        self.assertIsNone(cache.get("stats:total_books"))

    def test_pending_transaction_does_not_invalidate_availability_cache(self):
        """
        Creating a PENDING transaction should not clear availability cache
        since it doesn't affect book stock.
        """
        cache.set("stats:available_books", 100)

        Transaction.objects.create(
            user=self.user,
            book=self.book,
            status="PENDING",
            due_date=timezone.now() + timedelta(days=14),
        )

        self.assertEqual(cache.get("stats:available_books"), 100)


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

        stats = LibraryCacheService.get_homepage_stats()

        self.assertEqual(stats["total_books"], 5)
        self.assertEqual(stats["total_users"], 2)  # 2 active users
        self.assertEqual(stats["available_books"], 5)  # All books have available copies

    def test_get_cached_stats_caches_results(self):
        """get_cached_stats should cache results in configured cache backend."""
        # First call - should query DB and cache
        stats = LibraryCacheService.get_homepage_stats()

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
        stats1 = LibraryCacheService.get_homepage_stats()

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
        cache.set("stats:available_books", stats1["available_books"], timeout=60)

        # Second call - should use cache (old value)
        stats2 = LibraryCacheService.get_homepage_stats()

        # Should return cached value (not the new count)
        self.assertEqual(stats2["total_books"], stats1["total_books"])

    def test_get_cached_stats_handles_zero_books(self):
        """get_cached_stats should handle zero books gracefully."""
        stats = LibraryCacheService.get_homepage_stats()

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

        stats = LibraryCacheService.get_homepage_stats()

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

        stats = LibraryCacheService.get_homepage_stats()

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
        stats1 = LibraryCacheService.get_homepage_stats()
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
        stats2 = LibraryCacheService.get_homepage_stats()
        self.assertEqual(stats2["total_books"], initial_books + 1)

    def test_creating_user_invalidates_home_page_cache(self):
        """Creating a user should invalidate user stats cache."""
        # Get initial stats
        stats1 = LibraryCacheService.get_homepage_stats()
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
        stats2 = LibraryCacheService.get_homepage_stats()
        self.assertEqual(stats2["total_users"], initial_users + 1)


class AdminAnalyticsTests(TestCase):
    """Test get_admin_analytics caching and logic."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.book = Book.objects.create(
            title="Test Book",
            description="Test",
            isbn="1234567890123",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")
        self.book.genre.add(self.genre.pk)

    def test_get_admin_analytics_returns_correct_data(self):
        """Should return correct analytics data."""
        Transaction.objects.create(user=self.user, book=self.book, status="ISSUED")

        analytics = LibraryCacheService.get_admin_analytics()

        self.assertIn("trend_labels", analytics)
        self.assertIn("trend_data", analytics)
        # 1 transaction
        self.assertEqual(sum(analytics["trend_data"]), 1)

        self.assertIn("genre_labels", analytics)
        self.assertIn("FANTASY", analytics["genre_labels"])

        self.assertEqual(analytics["active_user_display"], self.user.user_code)

    def test_get_admin_analytics_caches_results(self):
        """Should cache results."""
        Transaction.objects.create(user=self.user, book=self.book, status="ISSUED")

        # First call caches
        analytics1 = LibraryCacheService.get_admin_analytics()
        self.assertEqual(sum(analytics1["trend_data"]), 1)

        # Verify cache key
        from caching import keys

        self.assertIsNotNone(cache.get(keys.DASHBOARD_ADMIN_ANALYTICS))

        # Create another transaction (bypassing signals that might invalidate if any -
        # but currently analytics cache is ONLY invalidated by invalidate_admin_kpis
        # which is called by invalidate_transaction_cache signal)
        # So to test caching, we need to manually set cache or mock signal?
        # Actually proper behavior is that it DOES invalidate on transaction change.
        # So let's disable signals or manually set cache to test retrieval.

        cache.set(keys.DASHBOARD_ADMIN_ANALYTICS, analytics1, timeout=60)

        # Modify DB directly to avoid signal (or just use set cache)
        # If we just read, it should get from cache.
        analytics2 = LibraryCacheService.get_admin_analytics()
        self.assertEqual(analytics2, analytics1)


class RelatedBooksCachingTests(TestCase):
    """Test get_related_books caching."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.genre, _ = Genre.objects.get_or_create(name="FANTASY")

        self.book1 = Book.objects.create(
            title="Book 1",
            description="Test",
            isbn="1111111111111",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        self.book1.genre.add(self.genre.id)

        self.book2 = Book.objects.create(
            title="Book 2",
            description="Test",
            isbn="2222222222222",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        self.book2.genre.add(self.genre.id)

    def test_get_related_books_returns_correct_books(self):
        """Should return books with same genre."""
        related = LibraryCacheService.get_related_books(
            self.book1.book_id, [self.genre.id]
        )
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0].book_id, self.book2.book_id)

    def test_get_related_books_caches_results(self):
        """Should cache related books."""
        LibraryCacheService.get_related_books(self.book1.book_id, [self.genre.id])

        # Check cache
        from caching import keys

        key = keys.RELATED_BOOKS.format(self.book1.book_id)
        self.assertIsNotNone(cache.get(key))

        # Create a new book that would be related
        book3 = Book.objects.create(
            title="Book 3",
            description="Test",
            isbn="3333333333333",
            author="Author",
            publication_date=datetime.date(2020, 1, 1),
            total_copies=5,
            copies_available=5,
            added_by=self.user,
        )
        book3.genre.add(self.genre.id)

        # Second call should return cached result (missing book3)
        related2 = LibraryCacheService.get_related_books(
            self.book1.book_id, [self.genre.id]
        )
        self.assertEqual(len(related2), 1)
        self.assertEqual(related2[0].book_id, self.book2.book_id)
