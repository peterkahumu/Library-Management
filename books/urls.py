from django.urls import path

from .views import (
    BookListView,
    BookDetailView,
    BookCreateView,
    BookEditView,
    GoogleBooksSearchView,
    GoogleBooksDetailView,
    GoogleBooksAddView,
)

urlpatterns = [
    path("", BookListView.as_view(), name="book_list"),
    path("<uuid:pk>/", BookDetailView.as_view(), name="book_detail"),
    path("new/", BookCreateView.as_view(), name="book_create"),
    path("<uuid:pk>/edit/", BookEditView.as_view(), name="book_edit"),
    # Google Books API routes
    path(
        "google-books/search/",
        GoogleBooksSearchView.as_view(),
        name="google_books_search",
    ),
    path(
        "google-books/detail/<str:volume_id>/",
        GoogleBooksDetailView.as_view(),
        name="google_books_detail",
    ),
    path(
        "google-books/add/<str:volume_id>/",
        GoogleBooksAddView.as_view(),
        name="google_books_add",
    ),
]
