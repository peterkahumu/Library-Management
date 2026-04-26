"""Create global context related to books."""

from caching.services import LibraryCacheService


def genres_context(request):
    """
    Returns a global context with genre information
    Retrieve data from Redis or database via the LibraryCacheService
    """
    return LibraryCacheService.get_genres_context_data()
