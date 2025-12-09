from django.db.models.signals import post_migrate, post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Genre, Book
from .constants import GENRE_CHOICES


@receiver(post_migrate)
def create_genres(sender, **kwargs):
    if sender.label == "books":
        for value, _ in GENRE_CHOICES:
            Genre.objects.get_or_create(name=value)


@receiver([post_save, post_delete], sender=Book)
def invalidate_book_cache_stats(sender, instance, **kwargs):
    "Clear book related cache when user is a book is created, update, or deleted"
    # NB: Check pages.utils and pages.views for stats consumptions
    cache.delete("stats:total_books")
    cache.delete("stats:available_books")
