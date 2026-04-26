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
        "librarian/borrow-requests/",
        views.LibrarianBorrowRequestsView.as_view(),
        name="librarian_borrow_requests",
    ),
    path(
        "librarian/return-requests/",
        views.LibrarianReturnRequestsView.as_view(),
        name="librarian_return_requests",
    ),
    # Action URLs
    path(
        "approve-borrow/<uuid:pk>/",
        views.ApproveBorrowView.as_view(),
        name="approve_borrow",
    ),
    path(
        "reject-borrow/<uuid:pk>/",
        views.RejectBorrowView.as_view(),
        name="reject_borrow",
    ),
    path(
        "approve-return/<uuid:pk>/",
        views.ApproveReturnView.as_view(),
        name="approve_return",
    ),
    path(
        "reject-return/<uuid:pk>/",
        views.RejectReturnView.as_view(),
        name="reject_return",
    ),
]
