# caching/services.py

import logging
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone
from django.db.models.functions import (
    TruncMonth,
    ExtractWeekDay,
    ExtractHour,
)
from . import keys

# Required model imports for database fallbacks
from books.models import Book, Genre
from accounts.models import LibraryUser, UserRoles
from book_circulation.models import Transaction
from datetime import timedelta

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

    @classmethod
    def get_related_books(cls, book_id, genre_ids):
        """Consumption: books/views.py (BookDetailView)"""
        key = keys.RELATED_BOOKS.format(book_id)

        def fetch():
            if not genre_ids:
                return []
            return list(
                Book.objects.filter(genre__in=genre_ids)
                .exclude(book_id=book_id)
                .distinct()[:5]
            )

        # Cache for 24 hours as recommendations don't need to be real-time
        return cls._get_or_set(key, fetch, timeout=keys.CACHE_1_DAY)

    @classmethod
    def get_admin_analytics(cls):
        """
        Consumption: dashboards/views.py (AdminDashboardView)
        Caches the default view (Monthly frequency, last 180 days).
        """

        def fetch():
            # Default time limit: 180 days
            time_limit = timezone.now() - timedelta(days=180)
            queryset = Transaction.objects.filter(
                status__in=["ISSUED", "RETURNED"], checkout_date__gte=time_limit
            ).select_related("book", "user")

            # 1. Borrowing Trends (Monthly)
            borrowing_trends = (
                queryset.annotate(period=TruncMonth("checkout_date"))
                .values("period")
                .annotate(count=Count("pk"))
                .order_by("period")
            )

            trend_labels = [
                entry["period"].strftime("%b %Y") for entry in borrowing_trends
            ]
            trend_data = [entry["count"] for entry in borrowing_trends]

            # 2. Popular Genres
            popular_genres = (
                queryset.values("book__genre__name")
                .annotate(count=Count("pk"))
                .order_by("-count")[:5]
            )
            genre_labels = [
                entry["book__genre__name"]
                for entry in popular_genres
                if entry["book__genre__name"]
            ]
            genre_data = [
                entry["count"] for entry in popular_genres if entry["book__genre__name"]
            ]

            # 3. Most active day
            active_day_aggregation = (
                queryset.annotate(day=ExtractWeekDay("checkout_date"))
                .values("day")
                .annotate(count=Count("pk"))
                .order_by("-count", "day")
            ).first()

            day_map = {
                1: "Sunday",
                2: "Monday",
                3: "Tuesday",
                4: "Wednesday",
                5: "Thursday",
                6: "Friday",
                7: "Saturday",
            }
            active_day = (
                day_map.get(active_day_aggregation["day"])
                if active_day_aggregation
                else "N/A"
            )
            active_day_count = (
                active_day_aggregation["count"] if active_day_aggregation else 0
            )

            # 4. Most active hour
            active_hour_aggregation = (
                queryset.annotate(hour=ExtractHour("checkout_date"))
                .values("hour")
                .annotate(count=Count("pk"))
                .order_by("-count", "hour")
            ).first()

            active_hour = (
                f"{active_hour_aggregation['hour']:02d}:00"
                if active_hour_aggregation
                else "N/A"
            )
            active_hour_count = (
                active_hour_aggregation["count"] if active_hour_aggregation else 0
            )

            # 5. Most active user
            active_user_aggregation = (
                queryset.values("user__user_code")
                .annotate(count=Count("pk"))
                .order_by("-count")
            ).first()

            if active_user_aggregation:
                active_user_display = active_user_aggregation["user__user_code"]
                active_user_count = active_user_aggregation["count"]
            else:
                active_user_display = "N/A"
                active_user_count = 0

            return {
                "trend_labels": trend_labels,
                "trend_data": trend_data,
                "genre_labels": genre_labels,
                "genre_data": genre_data,
                "active_day": active_day,
                "active_day_count": active_day_count,
                "active_hour": active_hour,
                "active_hour_count": active_hour_count,
                "active_user_display": active_user_display,
                "active_user_count": active_user_count,
            }

        return cls._get_or_set(
            keys.DASHBOARD_ADMIN_ANALYTICS, fetch, timeout=keys.CACHE_1_HOUR
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

    def invalidate_admin_analytics():
        cache.delete(keys.DASHBOARD_ADMIN_ANALYTICS)
        logger.info("🧹 Cache Cleared: Admin Analytics")

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
                keys.DASHBOARD_ADMIN_ANALYTICS,
            ]
        )
        logger.info("🧹 Cache Cleared: Homepage Stats, Admin and Librarian KPIs")

    @staticmethod
    def invalidate_genres():
        """Invalidation: books/signals.py (Genre model)"""
        cache.delete_many([keys.GENRES_TOP_5, keys.GENRES_ALL])
        logger.info("🧹 Cache Cleared: Genre Context")
