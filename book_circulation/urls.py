# - Updated URLs
from django.urls import path
from . import views

urlpatterns = [
    # Student URLs
    path("borrow/<uuid:book_id>/", views.BorrowBookView.as_view(), name="borrow_book"),
    path("my-books/", views.MyBooksListView.as_view(), name="my_books"),
    path(
        "return-request/<uuid:pk>/",
        views.RequestReturnView.as_view(),
        name="request_return",
    ),
    # Librarian URLs
    path(
        "dashboard/", views.LibrarianDashboardView.as_view(), name="librarian_dashboard"
    ),
    # Action URLs
    path(
        "approve-borrow/<uuid:pk>/",
        views.ApproveBorrowView.as_view(),
        name="approve_borrow",
    ),
    path(
        "approve-return/<uuid:pk>/",
        views.ApproveReturnView.as_view(),
        name="approve_return",
    ),
]
