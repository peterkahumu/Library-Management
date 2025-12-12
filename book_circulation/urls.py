from django.urls import path
from . import views

urlpatterns = [
    # Student URLs
    path("borrow/<uuid:book_id>/", views.BorrowBookView.as_view(), name="borrow_book"),
    path("my-books/", views.MyBooksListView.as_view(), name="my_books"),
    # Librarian URLs
    path(
        "dashboard/", views.LibrarianDashboardView.as_view(), name="librarian_dashboard"
    ),
    # Action URLs (still function-based)
    path("approve/<int:transaction_id>/", views.approve_borrow, name="approve_borrow"),
    path("return/<int:transaction_id>/", views.return_book_action, name="return_book"),
]
