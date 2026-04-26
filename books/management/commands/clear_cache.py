from django.core.management.base import BaseCommand
from django.core.cache import cache
from books.utils import invalidate_cache


class Command(BaseCommand):
    help = "Clears the application cache (Redis)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing cache...")

        # 1. Clear application specific keys (using our utility)
        invalidate_cache()
        self.stdout.write(self.style.SUCCESS("Application keys invalidated."))

        # 2. Force clear everything (optional, but good for this specific bug)
        try:
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS("Full cache.clear() executed successfully.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Could not perform full cache clear: {e}")
            )

        self.stdout.write(self.style.SUCCESS("Done."))
