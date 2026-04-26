from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from book_circulation.models import Transaction
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = "create a super user."

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")
        Transaction.objects.all().delete()

        # 1. Create Users
        self.create_users()

        self.stdout.write(self.style.SUCCESS("Successfully seeded database!"))

    def create_users(self):
        # Librarian
        if not User.objects.filter(username=settings.ADMIN_USERNAME).exists():
            User.objects.create_superuser(
                email="admin@admin.com",
                username=settings.ADMIN_USERNAME,
                password=settings.ADMIN_PASSWORD,
                first_name="admin",
                last_name="admin",
            )
            self.stdout.write("Created admin: admin@admin.com")
        else:
            self.stdout.write("Admin user already exists. Skipping.")
