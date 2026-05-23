from django.core.management.base import BaseCommand
from books.models import Genre
from books.constants import GENRE_CHOICES


class Command(BaseCommand):
    help = "Populates the database with default genres from constants.py"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding genres...")

        count = 0
        for genre_code, label in GENRE_CHOICES:
            # get or create the genre by
            genre, created = Genre.objects.get_or_create(name=genre_code)
            if created:
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {count} new genres.")
        )
