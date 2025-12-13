from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from books.models import Book
from accounts.models import LibraryUser, UserRoles
from book_circulation.models import Transaction


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "dashboards/admin_dashboard.html"

    def test_func(self):
        """
        Limit access to admins only.
        """
        return self.request.user.role == UserRoles.ADMIN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # KPI Cards
        context["total_books"] = Book.objects.count()
        context["active_students"] = LibraryUser.objects.filter(
            role=UserRoles.STUDENT, is_active=True
        ).count()
        context["issued_books"] = Transaction.objects.filter(status="ISSUED").count()

        # overdue books calculation
        context["overdue_books"] = Transaction.objects.overdue().count()
        print(Transaction.objects.overdue())

        # Charts data
        # 1. Borrowing Trends (6 months ago.)
        six_months_ago = timezone.now() - timedelta(days=180)
        borrowing_trends = (
            Transaction.objects.filter(checkout_date__gte=six_months_ago)
            .annotate(month=TruncMonth("checkout_date"))
            .values("month")
            .annotate(count=Count("pk"))
            .order_by("month")
        )

        context["trend_labels"] = [
            entry["month"].strftime("%b %Y") for entry in borrowing_trends
        ]
        context["trend_data"] = [entry["count"] for entry in borrowing_trends]

        # chart 2. Popular genres
        popular_genres = (
            Transaction.objects.values("book__genre__name")
            .annotate(count=Count("pk"))
            .order_by("-count")[:5]
        )

        context["genre_labels"] = [
            entry["book__genre__name"]
            for entry in popular_genres
            if entry["book__genre__name"]
        ]
        context["genre_data"] = [
            entry["count"] for entry in popular_genres if entry["book__genre__name"]
        ]

        context["recent_activity"] = Transaction.objects.select_related(
            "user", "book"
        ).order_by("-checkout_date")[:5]

        return context
