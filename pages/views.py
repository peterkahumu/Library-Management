from django.views.generic import TemplateView
from django.shortcuts import redirect

from books.models import Book
from caching.services import LibraryCacheService
from accounts.models import UserRoles


# Create your views here.
class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role == UserRoles.ADMIN:
                return redirect("admin_dashboard")
            elif request.user.role == UserRoles.LIBRARIAN:
                return redirect("librarian_dashboard")
            elif request.user.role == UserRoles.STUDENT:
                return redirect("student_dashboard")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # get cached stats.
        stats = LibraryCacheService.get_homepage_stats()

        context["featured_books"] = Book.objects.filter(featured=True).prefetch_related(
            "genre"
        )
        context.update(stats)
        return context
