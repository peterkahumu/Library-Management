from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    TemplateView,
    FormView,
)
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.files.base import ContentFile
import requests

from .google_books import GoogleBooksAPI, GoogleBooksAPIError

from .models import Book
from .forms import BookForm, GoogleBookImportForm
from accounts.models import UserRoles
from caching.services import LibraryCacheService


# Create your views here.
class BookListView(ListView):
    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_genre"] = self.request.GET.get("genre", "all")
        context["query"] = self.request.GET.get("query", "")
        return context

    def get_queryset(self):
        queryset = Book.objects.prefetch_related("genre").all()
        genre = self.request.GET.get("genre", "")
        query = self.request.GET.get("query", "")

        if genre and genre.lower() != "all":
            queryset = queryset.filter(genre__name__icontains=genre)

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(author__icontains=query)
                | Q(isbn__icontains=query)
            )

        return queryset.distinct()


class BookDetailView(DetailView):
    model = Book
    template_name = "books/book_detail.html"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("genre")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = context["object"]
        genres = book.genre.all()
        context["genres"] = [g.name for g in genres]

        if genres:
            context["related_books"] = LibraryCacheService.get_related_books(
                book.book_id, [g.id for g in genres]
            )
        else:
            context["related_books"] = []
        return context


class BookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.added_by = self.request.user
        self.object.save()
        form.save_m2m()
        return redirect(reverse("book_detail", kwargs={"pk": self.object.pk}))

    def test_func(self):
        return self.request.user.role in [UserRoles.ADMIN, UserRoles.LIBRARIAN]


class BookEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"

    def test_func(self):
        return (
            self.request.user.role in ["admin", "librarian"]
            or self.get_object().added_by == self.request.user
        )


# ============================================================================
# Google Books API Views
# ============================================================================
class GoogleBooksSearchView(LoginRequiredMixin, TemplateView):
    """
    Search for books using the Google Books API.

    Accessible to all logged in members
    """

    template_name = "books/google_books_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        filter_type = self.request.GET.get("filter", "all")
        page = self.request.GET.get("page", 1)

        context["query"] = query
        context["filter_type"] = filter_type
        context["results"] = []
        context["total_items"] = 0
        context["error"] = None

        if query:
            try:
                api = GoogleBooksAPI()

                # Construct search query with filter
                search_query = query
                if filter_type == "title":
                    search_query = f"intitle:{query}"
                elif filter_type == "author":
                    search_query = f"inauthor:{query}"
                elif filter_type == "isbn":
                    search_query = f"isbn:{query}"
                elif filter_type == "publisher":
                    search_query = f"inpublisher:{query}"

                # Calculate start index for pagination
                items_per_page = 20
                try:
                    page_num = int(page)
                except (ValueError, TypeError):
                    page_num = 1

                start_index = (page_num - 1) * items_per_page

                # Perform search
                search_results = api.search_books(
                    query=search_query,
                    start_index=start_index,
                    max_results=items_per_page,
                )

                # Normalize image links to HTTPS
                results = search_results.get("items", [])
                for item in results:
                    if "volumeInfo" in item:
                        api.normalize_image_links(item["volumeInfo"])

                context["results"] = results
                context["total_items"] = search_results.get("total_items", 0)
                context["current_page"] = page_num
                context["items_per_page"] = items_per_page

                # Calculate pagination info
                total_pages = (
                    context["total_items"] + items_per_page - 1
                ) // items_per_page
                total_pages = min(total_pages, 50)  # Limit to 50 pages

                context["total_pages"] = total_pages
                context["is_paginated"] = total_pages > 1

                # Create a mock page object for the pagination template
                class MockPage:
                    def __init__(self, number, num_pages):
                        self.number = number
                        self.num_pages = num_pages

                    @property
                    def has_previous(self):
                        return self.number > 1

                    @property
                    def has_next(self):
                        return self.number < self.num_pages

                    @property
                    def previous_page_number(self):
                        return self.number - 1

                    @property
                    def next_page_number(self):
                        return self.number + 1

                class MockPaginator:
                    def __init__(self, num_pages):
                        self.num_pages = num_pages
                        self.page_range = range(1, num_pages + 1)

                context["page_obj"] = MockPage(page_num, total_pages)
                context["paginator"] = MockPaginator(total_pages)

            except GoogleBooksAPIError as e:
                context["error"] = str(e)
                messages.error(self.request, f"Google Books API Error: {e}")
            except Exception:
                context["error"] = "An unexpected error occurred while searching."
                messages.error(
                    self.request, "An unexpected error occurred during search."
                )

        return context


class GoogleBooksDetailView(LoginRequiredMixin, TemplateView):
    """
    Display detailed information about a book from Google Books.

    Accessible to all  logged in members.
    """

    template_name = "books/google_books_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        volume_id = kwargs.get("volume_id")

        context["volume"] = None
        context["error"] = None
        context["isbn_exists"] = False

        if volume_id:
            try:
                api = GoogleBooksAPI()
                volume = api.get_book_details(volume_id)

                if volume:
                    # Normalize image links to HTTPS
                    if "volumeInfo" in volume:
                        api.normalize_image_links(volume["volumeInfo"])

                    context["volume"] = volume

                    # Check if book already exists in library
                    volume_info = volume.get("volumeInfo", {})
                    isbn = api.extract_isbn(volume_info)

                    if isbn:
                        # Clean ISBN for comparison
                        isbn_clean = isbn.replace("-", "").replace(" ", "")
                        context["isbn_exists"] = Book.objects.filter(
                            isbn=isbn_clean
                        ).exists()
                        context["isbn"] = isbn_clean
                else:
                    context["error"] = "Book not found."
                    messages.warning(self.request, "Book not found in Google Books.")

            except GoogleBooksAPIError as e:
                context["error"] = str(e)
                messages.error(self.request, f"Google Books API Error: {e}")
            except Exception:
                context["error"] = "An unexpected error occurred."
                messages.error(self.request, "Failed to retrieve book details.")

        return context


class GoogleBooksAddView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    Import a book from Google Books into the library.

    Only accessible to admins and librarians.
    """

    template_name = "books/book_form.html"
    form_class = GoogleBookImportForm

    def test_func(self):
        """Only allow admins and librarians."""
        return self.request.user.role in [UserRoles.ADMIN, UserRoles.LIBRARIAN]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        volume_id = self.kwargs.get("volume_id")

        context["volume"] = None
        context["error"] = None

        if volume_id:
            try:
                api = GoogleBooksAPI()
                volume = api.get_book_details(volume_id)

                # Normalize image links to HTTPS
                if volume and "volumeInfo" in volume:
                    api.normalize_image_links(volume["volumeInfo"])

                context["volume"] = volume
            except GoogleBooksAPIError as e:
                context["error"] = str(e)
                messages.error(self.request, f"Google Books API Error: {e}")
            except Exception:
                context["error"] = "Failed to retrieve book details."
                messages.error(self.request, "Failed to retrieve book details.")

        return context

    def get_form_kwargs(self):
        """Pass Google Books data to the form."""
        kwargs = super().get_form_kwargs()
        volume_id = self.kwargs.get("volume_id")

        if volume_id:
            try:
                api = GoogleBooksAPI()
                volume = api.get_book_details(volume_id)
                kwargs["google_data"] = volume
            except Exception:
                pass  # Form will handle missing data

        return kwargs

    def form_valid(self, form):
        """Save the book to the library."""
        try:
            # Create book instance but don't save yet
            book = form.save(commit=False)
            book.added_by = self.request.user

            # Handle cover image from Google Books
            volume_id = self.kwargs.get("volume_id")
            if volume_id:
                try:
                    api = GoogleBooksAPI()
                    volume = api.get_book_details(volume_id)
                    volume_info = volume.get("volumeInfo", {})

                    cover_url = api.extract_cover_url(volume_info)
                    if cover_url:
                        try:
                            response = requests.get(cover_url, timeout=10)
                            if response.status_code == 200:
                                filename = f"google_books_{volume_id}.jpg"
                                book.cover_image.save(
                                    filename, ContentFile(response.content), save=False
                                )
                        except Exception:
                            messages.warning(
                                self.request,
                                "There was an error in processing the image for this book."  # noqa
                                "We shall use a defaul image instead for now.",
                            )

                except Exception:
                    messages.error(
                        self.request,
                        "Book details not fully downloaded from Google books."
                        "We shall use a default image instead.",
                    )
            # Save the book
            book.save()
            form.save_m2m()

            messages.success(
                self.request, f'Successfully added "{book.title}" to the library!'
            )
            return redirect(reverse("book_detail", kwargs={"pk": book.pk}))

        except Exception as e:
            messages.error(self.request, f"Failed to add book to library: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission."""
        messages.error(
            self.request, "Please correct the errors below to add this book."
        )
        return super().form_invalid(form)
