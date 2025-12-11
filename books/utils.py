def invalidate_cache():
    from django.core.cache import cache

    """
    Clear all cache related to books on books creation, update and/or deletion
    """
    cache.delete("stats:total_books")
    cache.delete("stats:available_books")
