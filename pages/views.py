from django.views.generic import TemplateView
from books.models import Genre
from django.db.models import Count


# Create your views here.
class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genres"] = Genre.objects.annotate(book_count=Count("books")).order_by(
            "-book_count"
        )[:5]
        return context
