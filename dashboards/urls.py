from django.urls import path
from .views import AdminDashboardView

urlpatterns = [
    path("admin/", AdminDashboardView.as_view(), name="admin_dashboard"),
]
