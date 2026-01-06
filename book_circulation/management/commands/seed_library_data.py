import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from books.models import Book, Genre
from book_circulation.models import Transaction
from accounts.models import UserRoles

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with test users, books, and transactions."

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")
        Transaction.objects.all().delete()

        # 1. Create Users
        self.create_users()

        # 2. Create Books
        books = self.create_books()

        # 3. Create Transactions
        self.create_transactions(books)

        self.stdout.write(self.style.SUCCESS("Successfully seeded database!"))

    def create_users(self):

        # Librarian
        if not User.objects.filter(username="librarian").exists():
            User.objects.create_user(
                email="librarian@library.com",
                username="librarian",
                password="password123",
                first_name="Lydia",
                last_name="Librarian",
                role=UserRoles.LIBRARIAN,
            )
            self.stdout.write("Created Librarian: librarian@library.com / password123")
        else:
            self.stdout.write("Librarian user already exists. Skipping.")

        # Students
        for i in range(1, 4):
            username = f"student{i}"
            email = f"student{i}@library.com"
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    email=email,
                    username=username,
                    password="password123",
                    first_name="Student",
                    last_name=f"{i}",
                    role=UserRoles.STUDENT,
                )
                self.stdout.write(f"Created Student: {email} / password123")
            else:
                self.stdout.write(f"Student {username} already exists. Skipping.")

    def create_books(self):
        books_data = [
            ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction"),
            ("A Brief History of Time", "Stephen Hawking", "Science"),
            ("Sapiens", "Yuval Noah Harari", "History"),
            ("Clean Code", "Robert C. Martin", "Technology"),
            ("The Republic", "Plato", "Philosophy"),
            ("1984", "George Orwell", "Fiction"),
            ("The Pragmatic Programmer", "Andrew Hunt", "Technology"),
            ("Cosmos", "Carl Sagan", "Science"),
        ]

        # Get admin user for 'added_by' field
        admin_user = User.objects.filter(role=UserRoles.ADMIN).first()
        if not admin_user:
            # Fallback if admin creation was skipped or failed (should exist by now)
            admin_user = User.objects.create_superuser(
                email="fallback_admin@library.com",
                username="fallback_admin",
                password="password123",
                role=UserRoles.ADMIN,
            )

        created_books = []
        for title, author, genre_name in books_data:
            genre, _ = Genre.objects.get_or_create(name=genre_name)

            # Prepare defaults without ManyToMany fields
            defaults = {
                "author": author,
                "isbn": str(random.randint(1000000000000, 9999999999999)),
                "total_copies": 5,
                "copies_available": 5,
                "description": f"A classic book about {genre_name.lower()}.",
                "publication_date": timezone.now().date(),
                "added_by": admin_user,
            }

            book, created = Book.objects.get_or_create(title=title, defaults=defaults)

            # ManyToMany fields must be added after creation
            book.genre.add(genre)

            created_books.append(book)

        return created_books

    def create_transactions(self, books):
        students = User.objects.filter(role=UserRoles.STUDENT)
        if not students.exists():
            return

        # Clear existing transactions for clean slate (optional, but good for testing)
        # Transaction.objects.all().delete()

        for student in students:
            # 1. Active Loan (Issued)
            # Find a book with available copies
            available_books = [b for b in Book.objects.all() if b.copies_available > 0]
            if available_books:
                book = random.choice(available_books)
                if not Transaction.objects.filter(
                    user=student, book=book, status__in=["ISSUED", "PENDING"]
                ).exists():
                    Transaction.objects.create(
                        user=student,
                        book=book,
                        status="ISSUED",
                        checkout_date=timezone.now() - timedelta(days=5),
                        due_date=timezone.now() + timedelta(days=9),
                        is_ebook=False,
                    )

            # 2. Overdue Loan
            # Re-fetch available hooks just in case
            available_books = [b for b in Book.objects.all() if b.copies_available > 0]
            if available_books:
                book = random.choice(available_books)
                if not Transaction.objects.filter(
                    user=student, book=book, status__in=["ISSUED", "PENDING"]
                ).exists():
                    Transaction.objects.create(
                        user=student,
                        book=book,
                        status="ISSUED",
                        checkout_date=timezone.now() - timedelta(days=20),
                        due_date=timezone.now() - timedelta(days=5),  # Overdue by 5 days
                        is_ebook=False,
                    )

            # 3. Pending Borrow Request
            book = random.choice(books)
            if not Transaction.objects.filter(
                user=student, book=book, status__in=["ISSUED", "PENDING"]
            ).exists():
                Transaction.objects.create(
                    user=student,
                    book=book,
                    status="PENDING",
                    checkout_date=timezone.now(),
                    due_date=timezone.now() + timedelta(days=14),
                    is_ebook=False,
                )

            # 4. Pending Return Request
            book = random.choice(books)
            if not Transaction.objects.filter(
                user=student, book=book, status__in=["ISSUED", "PENDING"]
            ).exists():
                Transaction.objects.create(
                    user=student,
                    book=book,
                    status="RETURN_REQUESTED",
                    checkout_date=timezone.now() - timedelta(days=10),
                    due_date=timezone.now() + timedelta(days=4),
                    is_ebook=False,
                )

            # 5. History (Returned)
            for _ in range(3):
                book = random.choice(books)
                Transaction.objects.create(
                    user=student,
                    book=book,
                    status="RETURNED",
                    checkout_date=timezone.now() - timedelta(days=60),
                    due_date=timezone.now() - timedelta(days=46),
                    returned_date=timezone.now()
                    - timedelta(days=random.randint(40, 50)),
                    is_ebook=False,
                )

            # 6. Yesterday
            for _ in range(3):
                book = random.choice(books)
                Transaction.objects.create(
                    user=student,
                    book=book,
                    status="RETURNED",
                    checkout_date=timezone.now() - timedelta(days=1),
                    due_date=timezone.now() + timedelta(days=5),
                    returned_date=timezone.now() + timedelta(days=random.randint(0, 5)),
                    is_ebook=False,
                )

            # 7. 2 days ago
            for _ in range(3):
                book = random.choice(books)
                Transaction.objects.create(
                    user=student,
                    book=book,
                    status="RETURNED",
                    checkout_date=timezone.now() - timedelta(days=2),
                    due_date=timezone.now() + timedelta(days=5),
                    returned_date=timezone.now() + timedelta(days=random.randint(0, 5)),
                    is_ebook=False,
                )

        self.stdout.write(f"Created transactions for {students.count()} students.")
