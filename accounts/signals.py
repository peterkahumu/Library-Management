from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


from caching.services import LibraryCacheService
from .models import LibraryUser


@receiver([post_save, post_delete], sender=LibraryUser)
def invalidate_user_cache_stats(sender, instance, **kwargs):
    """
    Clear user related cache when user is created, updated, or deleted
    """
    # NB: pages.views for stats consumptions
    LibraryCacheService.invalidate_total_users()
    LibraryCacheService.invalidate_admin_kpis()
