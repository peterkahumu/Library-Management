def invalidate_cache():
    """
    Clear all cache related to books on books creation, update and/or deletion
    """
    from django.core.cache import cache

    cache.delete("stats:total_books")
    cache.delete("stats:available_books")
