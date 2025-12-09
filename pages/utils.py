import logging
from django.core.cache import cache

from books.models import Book
from accounts.models import LibraryUser

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 60 * 60 * 24  # one day.


def get_cached_stats():
    """Get Cached statistics for the homepage."""

    total_books = cache.get("stats:total_books")
    total_users = cache.get("stats:total_users")
    available_books = cache.get("stats:available_books")

    if total_books is None:
        logging.info("🔴 DB: retrieval of total books...")
        total_books = Book.objects.count()
        cache.set("stats:total_books", total_books, CACHE_TIMEOUT)
    else:
        logging.info("🟢 Cache: retrieval of total books")

    if total_users is None:
        logging.info("🔴 DB: retrieval of total users...")
        total_users = LibraryUser.objects.filter(is_active=True).count()
        cache.set("stats:total_users", total_users, CACHE_TIMEOUT)
    else:
        logging.info("🟢 Cache: retrieval of total users")

    if available_books is None:
        logging.info("🔴 DB: retrieval of available books")
        available_books = Book.objects.filter(copies_available__gt=0).count()
        cache.set("stats:available_books", available_books, CACHE_TIMEOUT)
    else:
        logging.info("🟢 Cache: retrieval of available books")

    return {
        "total_books": total_books,
        "total_users": total_users,
        "available_books": available_books,
    }
