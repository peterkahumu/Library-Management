# dashboards/urls.py

from django.urls import path
from .views import AdminDashboardView, TransactionLogsView, UserRoleUpdateView

urlpatterns = [
    # Admin Dashboard (Charts, KPIs)
    path("admin/", AdminDashboardView.as_view(), name="admin_dashboard"),
    # Detailed Logs Page (for pagination and detailed filtering)
    path("logs/", TransactionLogsView.as_view(), name="transaction_logs"),
    # User Role Management Action
    path("role-update/", UserRoleUpdateView.as_view(), name="user_role_update"),
]
