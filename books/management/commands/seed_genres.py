from django.core.management.base import BaseCommand
from books.models import Genre
from books.constants import GENRE_CHOICES

class Command(BaseCommand):
    help = 'Populates the database with default genres from constants.py'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding genres...")
        
        count = 0
        for code, label in GENRE_CHOICES:
            # We use the code (value) as the name, or the label?
            # Looking at signals.py, it uses 'value' which corresponds to the first element (e.g. 'ADVENTURE')
            # However, looking at the previous user complaint about "history" vs "History", 
            # and the constants.py file:
            # ("ADVENTURE", "Adventure"),
            # The signal uses: Genre.objects.get_or_create(name=value) -> name="ADVENTURE"
            # Wait, let me double check the signals.py content from previous turns.
            
            # Step 122 view_file output:
            # for value, _ in GENRE_CHOICES:
            #     Genre.objects.get_or_create(name=value)
            
            # So it uses the uppercase code. 
            # If the frontend expects "Adventure", then `name` should probably be the label?
            # Let's check `books/models.py`. 
            # name = models.CharField(max_length=50, choices=GENRE_CHOICES, unique=True)
            # def __str__(self): return dict(self._meta.get_field("name").choices).get(self.name, self.name)
            
            # So the DB stores "ADVENTURE", and __str__ converts it to "Adventure".
            # The duplication issue "history" vs "History" implies something was storing raw strings not in choices.
            # So restoring using the keys (ADVENTURE) is the correct, intended behavior.
            
            genre, created = Genre.objects.get_or_create(name=code)
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} new genres."))
