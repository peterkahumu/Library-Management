from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Genre
from .constants import GENRE_CHOICES


@receiver(post_migrate)
def create_genres(sender, **kwargs):
    if sender.label == "books":
        for value, _ in GENRE_CHOICES:
            Genre.objects.get_or_create(name=value)
