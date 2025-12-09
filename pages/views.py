from django.views.generic import TemplateView

from books.models import Book
from .utils import get_cached_stats


# Create your views here.
class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # get cached stats.
        stats = get_cached_stats()

        context["featured_books"] = Book.objects.filter(featured=True).prefetch_related(
            "genre"
        )
        context.update(stats)
        return context
