# caching/services.py

import logging
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone
from . import keys

# Required model imports for database fallbacks
from books.models import Book, Genre
from accounts.models import LibraryUser, UserRoles
from book_circulation.models import Transaction

logger = logging.getLogger(__name__)


class LibraryCacheService:
    """
    Central service for all caching logic.
    Consumption and Invalidation points are noted in docstrings.
    """

    @staticmethod
    def _get_or_set(key, fetch_func, timeout=keys.CACHE_1_DAY):
        """Internal helper for get-or-set patterns."""
        data = cache.get(key)
        if data is None:
            logger.info(f"🔴 DB Retrieval: {key}")
            data = fetch_func()
            cache.set(key, data, timeout)
        else:
            logger.info(f"🟢 Cache Retrieval: {key}")
        return data

    @classmethod
    def get_homepage_stats(cls):
        """Consumption: pages/views.py"""

        def fetch():
            return {
                "total_books": Book.objects.count(),
                "total_users": LibraryUser.objects.filter(is_active=True).count(),
                "available_books": Book.objects.filter(copies_available__gt=0).count(),
            }

        total_books = cls._get_or_set(
            keys.STATS_TOTAL_BOOKS, lambda: Book.objects.count()
        )
        total_users = cls._get_or_set(
            keys.STATS_TOTAL_USERS,
            lambda: LibraryUser.objects.filter(is_active=True).count(),
        )
        available_books = cls._get_or_set(
            keys.STATS_AVAILABLE_BOOKS,
            lambda: Book.objects.filter(copies_available__gt=0).count(),
        )

        return {
            "total_books": total_books,
            "total_users": total_users,
            "available_books": available_books,
        }

    @classmethod
    def get_genres_context_data(cls):
        """Consumption: books/context_processors.py"""
        top_5 = cls._get_or_set(
            keys.GENRES_TOP_5,
            lambda: list(
                Genre.objects.annotate(book_count=Count("books")).order_by(
                    "-book_count"
                )[:5]
            ),
        )
        all_genres = cls._get_or_set(keys.GENRES_ALL, lambda: list(Genre.objects.all()))
        return {"top_5_genres": top_5, "all_genres": all_genres}

    @classmethod
    def get_admin_kpis(cls):
        """Consumption: dashboards/views.py (AdminDashboardView)"""

        def fetch():
            return {
                "total_books": Book.objects.count(),
                "active_students": LibraryUser.objects.filter(
                    role=UserRoles.STUDENT, is_active=True
                ).count(),
                "issued_books": Transaction.objects.filter(status="ISSUED").count(),
                "active_digital_loans": Transaction.objects.filter(
                    status="DOWNLOADED"
                ).count(),
                "overdue_books": Transaction.objects.filter(
                    status="ISSUED", due_date__lt=timezone.now()
                ).count(),
            }

        return cls._get_or_set(
            keys.DASHBOARD_ADMIN_KPIS, fetch, timeout=keys.CACHE_1_HOUR
        )

    @classmethod
    def get_librarian_kpis(cls):
        """Consumption: dashboards/views.py (LibrarianDashboardView)"""

        def fetch():
            # Date filtering
            today_start = timezone.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return {
                "issued_today_count": Transaction.objects.filter(
                    status__in=["ISSUED", "RETURN_REQUESTED", "RETURNED"],
                    checkout_date__gte=today_start,
                ).count(),
                "returned_today_count": Transaction.objects.filter(
                    status="RETURNED", returned_date__gte=today_start, is_ebook=False
                ).count(),
                "active_digital_loans": Transaction.objects.filter(
                    status="DOWNLOADED"
                ).count(),
                "total_overdue_count": Transaction.objects.overdue().count(),
                "pending_borrow_count": Transaction.objects.filter(
                    status="PENDING"
                ).count(),
                "pending_return_count": Transaction.objects.filter(
                    status="RETURN_REQUESTED"
                ).count(),
            }

        return cls._get_or_set(
            keys.DASHBOARD_LIBRARIAN_KPIS, fetch, timeout=keys.CACHE_1_HOUR
        )

    @staticmethod
    def invalidate_total_books():
        cache.delete(keys.STATS_TOTAL_BOOKS)
        logger.info("🧹 Cache Cleared: Total Books")

    @staticmethod
    def invalidate_total_users():
        cache.delete(keys.STATS_TOTAL_USERS)
        logger.info("🧹 Cache Cleared: Total Users")

    @staticmethod
    def invalidate_available_books():
        cache.delete(keys.STATS_AVAILABLE_BOOKS)
        logger.info("🧹 Cache Cleared: Available Books")

    @staticmethod
    def invalidate_admin_kpis():
        cache.delete(keys.DASHBOARD_ADMIN_KPIS)
        logger.info("🧹 Cache Cleared: Admin KPIs")

    @staticmethod
    def invalidate_librarian_kpis():
        cache.delete(keys.DASHBOARD_LIBRARIAN_KPIS)
        logger.info("🧹 Cache Cleared: Librarian KPIs")

    @staticmethod
    def invalidate_all_stats():
        """
        Invalidation: books/signals.py, accounts/signals.py, book_circulation/signals.py
        DEPRECATED: Use granular invalidation methods instead.
        """
        cache.delete_many(
            [
                keys.STATS_TOTAL_BOOKS,
                keys.STATS_TOTAL_USERS,
                keys.STATS_AVAILABLE_BOOKS,
                keys.DASHBOARD_ADMIN_KPIS,
                keys.DASHBOARD_LIBRARIAN_KPIS,
            ]
        )
        logger.info("🧹 Cache Cleared: Homepage Stats, Admin and Librarian KPIs")

    @staticmethod
    def invalidate_genres():
        """Invalidation: books/signals.py (Genre model)"""
        cache.delete_many([keys.GENRES_TOP_5, keys.GENRES_ALL])
        logger.info("🧹 Cache Cleared: Genre Context")
