from django.views.generic import TemplateView
from books.models import Book


# Create your views here.
class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_books"] = Book.objects.filter(featured=True).prefetch_related(
            "genre"
        )
        return context
