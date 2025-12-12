from django.db import models
from django.conf import settings
from books.models import Book


class Transaction(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ISSUED", "Issued"),
        ("RETURNED", "Returned"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="transactions"
    )
    checkout_date = models.DateTimeField(auto_now_add=True, db_index=True)
    due_date = models.DateTimeField(db_index=True)
    returned_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="ISSUED", db_index=True
    )
    is_ebook = models.BooleanField(default=False)

    class Meta:
        ordering = ["-checkout_date"]
        indexes = [models.Index(fields=["user", "status"])]

    def save(self, *args, **kwargs):
        """
        Only decrement stock when the book is physically checked out (ISSUED).
        """
        if not self.is_ebook:
            # Scenario 1: Librarian creates a new 'ISSUED' record directly
            if not self.pk and self.status == "ISSUED":
                if not self.book.borrow_book():
                    raise ValueError("Book not available.")

            # Scenario 2: Librarian updates 'PENDING' -> 'ISSUED'
            elif self.pk:
                original = Transaction.objects.get(pk=self.pk)
                if original.status == "PENDING" and self.status == "ISSUED":
                    if not self.book.borrow_book():
                        # multiple people made a request for the last copy.
                        # Issue to the first person
                        raise ValueError("Book is no longer available.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title} - {self.status}"
