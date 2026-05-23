from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import (
    TruncMonth,
    TruncYear,
    TruncDay,
    ExtractWeekDay,
    ExtractHour,
)
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import redirect
from django.views import View
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
import httpx
from caching.services import LibraryCacheService

from accounts.models import LibraryUser, UserRoles
from book_circulation.models import Transaction

import logging

logger = logging.getLogger(__name__)


def get_filtered_queryset(request):
    """
    Returns a queryset of Transactions filtered by frequency or custom date range.
    Used for dashboard charts and transaction logs.
    """
    queryset = Transaction.objects.filter(
        status__in=["ISSUED", "RETURNED"]
    ).select_related("book", "user")
    frequency = request.GET.get("frequency", "monthly")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if not start_date_str or not end_date_str:
        # Default range based on frequency
        if frequency == "monthly":
            time_limit = timezone.now() - timedelta(days=180)
        elif frequency == "annual":
            time_limit = timezone.now() - timedelta(days=365 * 3)
        else:
            time_limit = timezone.now() - timedelta(days=180)
        queryset = queryset.filter(checkout_date__gte=time_limit)
    else:
        # Manual date range
        try:
            start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = timezone.datetime.strptime(
                end_date_str, "%Y-%m-%d"
            ).date() + timedelta(days=1)
            queryset = queryset.filter(checkout_date__range=(start_date, end_date))
        except ValueError:
            # Invalid date format; notify user and fall back to default range
            messages.error(
                request,
                "Invalid date format for the selected range. Fallback to default range",
            )
            if frequency == "monthly":
                time_limit = timezone.now() - timedelta(days=180)
            elif frequency == "annual":
                time_limit = timezone.now() - timedelta(days=365 * 3)
            else:
                time_limit = timezone.now() - timedelta(days=180)
            queryset = queryset.filter(checkout_date__gte=time_limit)

    return queryset, frequency


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Dashboard view for Admins, providing KPI cards, charts, and analytics.
    """

    template_name = "dashboards/admin_dashboard.html"

    def test_func(self):
        """Only Admins can access this dashboard."""
        return self.request.user.role == UserRoles.ADMIN

    def get_context_data(self, **kwargs):
        """Builds the context for dashboard template."""
        context = super().get_context_data(**kwargs)
        queryset, frequency = get_filtered_queryset(self.request)
        context["frequency"] = frequency
        context["current_start_date"] = self.request.GET.get("start_date", "")
        context["current_end_date"] = self.request.GET.get("end_date", "")

        # KPI cards
        context.update(LibraryCacheService.get_admin_kpis())

        if (
            frequency == "monthly"
            and not context["current_start_date"]
            and not context["current_end_date"]
        ):
            context.update(LibraryCacheService.get_admin_analytics())
        else:
            # Calculate from queryset (fallback for custom filters)
            if frequency == "annual":
                trunc_func = TruncYear
                date_format = "%Y"
            elif frequency == "monthly":
                trunc_func = TruncMonth
                date_format = "%b %Y"
            else:
                trunc_func = TruncDay
                date_format = "%d"
                month_format = "%b"

            # Borrowing trends
            borrowing_trends = (
                queryset.annotate(period=trunc_func("checkout_date"))
                .values("period")
                .annotate(count=Count("pk"))
                .order_by("period")
            )

            labels = []
            last_month = None
            for entry in borrowing_trends:
                period = entry["period"]
                if frequency not in ["monthly", "annual"]:
                    month_label = (
                        period.strftime(month_format)
                        if period.month != last_month
                        else ""
                    )
                    last_month = period.month
                    label = f"{period.day} {month_label}".strip()
                else:
                    label = period.strftime(date_format)
                labels.append(label)

            context["trend_labels"] = labels
            context["trend_data"] = [entry["count"] for entry in borrowing_trends]

            # Popular genres
            popular_genres = (
                queryset.values("book__genre__name")
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

            # Most active day of the week
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
            context["active_day"] = (
                day_map.get(active_day_aggregation["day"])
                if active_day_aggregation
                else "N/A"
            )
            context["active_day_count"] = (
                active_day_aggregation["count"] if active_day_aggregation else 0
            )

            # Most active hour
            active_hour_aggregation = (
                queryset.annotate(hour=ExtractHour("checkout_date"))
                .values("hour")
                .annotate(count=Count("pk"))
                .order_by("-count", "hour")
            ).first()
            context["active_hour"] = (
                f"{active_hour_aggregation['hour']:02d}:00"
                if active_hour_aggregation
                else "N/A"
            )
            context["active_hour_count"] = (
                active_hour_aggregation["count"] if active_hour_aggregation else 0
            )

            # Most active user
            active_user_aggregation = (
                queryset.values(
                    "user__user_code", "user__first_name", "user__last_name"
                )
                .annotate(count=Count("pk"))
                .order_by("-count")
            ).first()
            if active_user_aggregation:
                context["active_user_display"] = active_user_aggregation[
                    "user__user_code"
                ]
                context["active_user_count"] = active_user_aggregation["count"]
            else:
                context["active_user_display"] = "N/A"
                context["active_user_count"] = 0

        # Recent activity table
        context["recent_activity"] = queryset.order_by("-checkout_date")[:3]

        # User management data
        context["all_users"] = LibraryUser.objects.filter(is_superuser=False).values(
            "user_code", "username"
        )
        context["all_roles"] = [
            role for role in UserRoles.choices if role[0] != UserRoles.ADMIN
        ]

        return context


class TransactionLogsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List view for filtering and paginating transaction logs.
    """

    model = Transaction
    template_name = "dashboards/transaction_logs.html"
    context_object_name = "transactions"
    paginate_by = 25

    def test_func(self):
        return self.request.user.role in [UserRoles.ADMIN, UserRoles.LIBRARIAN]

    def get_queryset(self):
        """
        Returns filtered queryset based on GET parameters: date, status, user, day, hour
        """
        queryset = (
            Transaction.objects.all()
            .select_related("user", "book")
            .order_by("-checkout_date")
        )
        date_str = self.request.GET.get("date")
        date_field = self.request.GET.get("date_field", "checkout_date")
        status = self.request.GET.get("status")
        user_code = self.request.GET.get("user_code")
        day_of_week = self.request.GET.get("day")
        hour_of_day = self.request.GET.get("hour")

        if date_str:
            try:
                # Security check: only allow specific date fields
                if date_field not in ["checkout_date", "returned_date", "due_date"]:
                    date_field = "checkout_date"

                date_obj = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
                # Use dictionary unpacking for dynamic field filtering
                filter_kwargs = {f"{date_field}__date": date_obj}
                queryset = queryset.filter(**filter_kwargs)
            except ValueError:
                pass  # fallback to original queryset
        if status:
            if status.upper() == "OVERDUE":
                queryset = queryset.filter(status="ISSUED", due_date__lt=timezone.now())
            elif "," in status:
                status_list = [s.strip().upper() for s in status.split(",")]
                queryset = queryset.filter(status__in=status_list)
            elif status.upper() == "DOWNLOADED":
                queryset = queryset.filter(status="DOWNLOADED")
            else:
                queryset = queryset.filter(status=status.upper())
        if user_code:
            try:
                user = LibraryUser.objects.get(user_code__iexact=user_code)
                queryset = queryset.filter(user=user)
            except LibraryUser.DoesNotExist:
                queryset = queryset.none()
        if day_of_week:
            day_map = {
                "sunday": 1,
                "monday": 2,
                "tuesday": 3,
                "wednesday": 4,
                "thursday": 5,
                "friday": 6,
                "saturday": 7,
            }
            day_num = day_map.get(day_of_week.lower())
            if day_num:
                queryset = queryset.annotate(
                    day=ExtractWeekDay("checkout_date")
                ).filter(day=day_num)
        if hour_of_day:
            try:
                hour_num = int(hour_of_day)
                queryset = queryset.annotate(hour=ExtractHour("checkout_date")).filter(
                    hour=hour_num
                )
            except (ValueError, TypeError):
                pass  # ignore and return the queryset without filtering.
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Transaction.STATUS_CHOICES
        context["current_date"] = self.request.GET.get("date", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_user_code"] = self.request.GET.get("user_code", "")
        context["current_day"] = self.request.GET.get("day", "")
        context["current_hour"] = self.request.GET.get("hour", "")
        return context


class UserRoleUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to update a user's role. Only accessible by Admins.
    """

    def test_func(self):
        return self.request.user.role == UserRoles.ADMIN

    def post(self, request, *args, **kwargs):
        user_code = request.POST.get("user_code")
        new_role = request.POST.get("new_role")
        redirect_url = request.POST.get("next", reverse("admin_dashboard"))

        if new_role not in [role[0] for role in UserRoles.choices]:
            messages.error(request, "Invalid role specified.")
            return redirect(redirect_url)

        try:
            user_to_update = LibraryUser.objects.get(user_code__iexact=user_code)
        except LibraryUser.DoesNotExist:
            messages.error(request, f"User with code {user_code} not found.")
            return redirect(redirect_url)

        if user_to_update == request.user:
            messages.warning(request, "You cannot change your own role.")
            return redirect(redirect_url)

        user_to_update.role = new_role
        user_to_update.save()
        messages.success(
            request, f"Role for user {user_code} updated to {new_role.title()}."
        )
        return redirect(redirect_url)


class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Dashboard view for Students, providing their borrowing history and status.
    """

    template_name = "dashboards/student_dashboard.html"

    def test_func(self):
        return self.request.user.role in [
            UserRoles.STUDENT,
            UserRoles.LIBRARIAN,
            UserRoles.ADMIN,
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user

        # KPI Metrics
        context["borrowed_books"] = Transaction.objects.filter(
            user=student, status="ISSUED"
        ).count()

        context["pending_requests"] = Transaction.objects.filter(
            user=student, status="PENDING"
        ).count()

        context["overdue_books"] = Transaction.objects.filter(
            user=student, status="ISSUED", due_date__lt=timezone.now()
        ).count()

        # Calculate estimated fines (simple logic: $1 per overdue day)
        overdue_txns = Transaction.objects.filter(
            user=student, status="ISSUED", due_date__lt=timezone.now()
        )
        total_fines = sum(txn.days_overdue for txn in overdue_txns)
        context["fines"] = total_fines

        # Fetch Recommendations
        rec_url = getattr(
            settings, "RECOMMENDATION_SERVICE_URL", "http://localhost:8002/"
        )
        personality_recs = []
        similarity_recs = []
        recent_txn = None

        try:
            with httpx.Client(timeout=5.0) as client:
                # Personality-based recommendations
                p_resp = client.post(
                    f"{rec_url}recommend/personality",
                    json={"user_id": str(student.user_id)},
                )
                if p_resp.status_code == 200:
                    personality_recs = p_resp.json().get("recommendations", [])

                # Similarity-based recommendations
                # Get the most recent borrowed book
                recent_txn = (
                    Transaction.objects.filter(user=student)
                    .order_by("-checkout_date")
                    .first()
                )
                if recent_txn:
                    s_resp = client.post(
                        f"{rec_url}recommend/similar",
                        json={"book_id": str(recent_txn.book_id), "limit": 5},
                    )
                    if s_resp.status_code == 200:
                        similarity_recs = s_resp.json().get("recommendations", [])
        except Exception as e:
            logger.info(f"Recommendation service is unavailable: {e}")

        context["personality_recommendations"] = personality_recs
        context["similarity_recommendations"] = similarity_recs
        context["similarity_basis"] = recent_txn.book if recent_txn else ""

        return context


class LibrarianDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "dashboards/librarian_dashboard.html"

    def test_func(self):
        return self.request.user.role in [UserRoles.LIBRARIAN, UserRoles.ADMIN]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Date filtering
        # KPI Metrics
        context.update(LibraryCacheService.get_librarian_kpis())

        context["recent_transactions"] = Transaction.objects.select_related(
            "user", "book"
        ).order_by("-checkout_date")[:2]
        return context
