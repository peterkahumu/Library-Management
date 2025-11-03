from django.views.generic import ListView

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
        return context
