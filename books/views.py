from django.views.generic import ListView, DetailView
from django.db.models import Q

from .models import Book, Genre


# Create your views here.
class BookListView(ListView):
    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genres"] = Genre.objects.all()
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

        print(genres)
        if genres.exists():
            context["related_books"] = (
                Book.objects.filter(genre__in=genres)
                .exclude(book_id=book.book_id)
                .distinct()[:5]
            )
        else:
            context["related_books"] = []

        return context
