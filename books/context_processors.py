"""Create global context related to books."""

from django.db.models import Count

from .models import Genre


def genres_context(request):
    """
    Returns a global context with top five genres based on book count.
    Return all genres in the database
    """
    top_5_genres = list(
        Genre.objects.annotate(book_count=Count("books")).order_by("-book_count")[:5]
    )
    all_genres = list(Genre.objects.all())
    context_data = {"top_5_genres": top_5_genres, "all_genres": all_genres}
    return context_data
