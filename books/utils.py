def invalidate_cache():
    """
    Clear all cache related to books on books creation, update and/or deletion
    """
    from caching.services import LibraryCacheService

    LibraryCacheService.invalidate_total_books()
    LibraryCacheService.invalidate_available_books()
    LibraryCacheService.invalidate_admin_kpis()
    LibraryCacheService.invalidate_genres()
