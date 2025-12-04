from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q, Count
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Book, Genre
from .forms import BookForm


# Create your views here.
def genres_context(request):
    """Returns a global context with top five genres based on book count."""
    genres = Genre.objects.annotate(book_count=Count("books")).order_by("-book_count")[
        :5
    ]
    all_genres = Genre.objects.all()

    return {"genres": genres, "all_genres": all_genres}


class BookListView(ListView):
    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for book in context["books"]:
            book.genre_names = " ".join(book.genre.values_list("name", flat=True))
        context["selected_genres"] = self.request.GET.get("genre", "all")
        context["query"] = self.request.GET.get("query", "")
        return context

    def get_queryset(self):
        queryset = Book.objects.all()
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = context["object"]
        genres = book.genre.all()
        context["genres"] = list(genres.values_list("name", flat=True))
        if genres.exists():
            context["related_books"] = (
                Book.objects.filter(genre__in=genres)
                .exclude(book_id=book.book_id)
                .distinct()[:5]
            )
        else:
            context["related_books"] = []
        return context


class BookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_create.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.added_by = self.request.user
        self.object.save()
        form.save_m2m()
        return redirect(reverse("book_detail", kwargs={"pk": self.object.pk}))

    def test_func(self):
        return self.request.user.role in ["admin", "librarian"]


class BookEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_edit.html"

    def test_func(self):
        return (
            self.request.user.role in ["admin", "librarian"]
            or self.get_object().added_by == self.request.user
        )
