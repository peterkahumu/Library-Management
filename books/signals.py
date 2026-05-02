from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .utils import invalidate_cache

from .models import Genre, Book


@receiver([post_save, post_delete], sender=Book)
@receiver([post_save, post_delete], sender=Genre)
def invalidate_book_cache_stats(sender, instance, **kwargs):
    "Clear book related cache when a book is created, updated, or deleted"
    # NB: Check pages.utils and pages.views for stats consumptions
    invalidate_cache()
