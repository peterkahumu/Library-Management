from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


from .models import LibraryUser


@receiver([post_save, post_delete], sender=LibraryUser)
def invalidate_user_cache_stats(sender, instance, **kwargs):
    """
    Clear user related cache when user are created, updated, or deleted
    """
    # NB: Check pages.utils and pages.views for stats consumptions
    cache.delete("stats:total_users")
