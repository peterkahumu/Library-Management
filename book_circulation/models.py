import uuid
from datetime import timedelta
from django.db import models, transaction as db_transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from books.models import Book


class TransactionManager(models.Manager):
    """Custom manager for Transaction queries."""

    def active(self):
        """Get all active (not returned) transactions."""
        return self.filter(status__in=["PENDING", "ISSUED", "RETURN_REQUESTED"])

    def overdue(self):
        """Get all overdue transactions."""
        return self.filter(
            status__in=["ISSUED", "RETURN_REQUESTED"], due_date__lt=timezone.now()
        )

    def for_user(self, user):
        """Get transactions for a specific user with related data."""
        return self.filter(user=user).select_related("book", "user")

    def for_book(self, book):
        """Get transactions for a specific book."""
        return self.filter(book=book).select_related("user")

    def returned_on_time(self):
        """Get transactions returned on or before due date."""
        return self.filter(status="RETURNED", returned_date__lte=models.F("due_date"))

    def returned_late(self):
        """Get transactions returned after due date."""
        return self.filter(status="RETURNED", returned_date__gt=models.F("due_date"))


class Transaction(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ISSUED", "Issued"),
        ("RETURN_REQUESTED", "Return Requested"),
        ("RETURNED", "Returned"),
    ]

    transaction_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="transactions"
    )
    checkout_date = models.DateTimeField(default=timezone.now, db_index=True)
    due_date = models.DateTimeField(db_index=True)
    returned_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="ISSUED", db_index=True
    )
    is_ebook = models.BooleanField(default=False)

    objects = TransactionManager()

    class Meta:
        ordering = ["-checkout_date"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["book", "status"]),
            models.Index(fields=["due_date", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(status="RETURNED", returned_date__isnull=True),
                name="returned_status_requires_date",
            ),
        ]

    def clean(self):
        """Validate transaction data before saving."""
        super().clean()

        if self.due_date and self.checkout_date:
            if self.due_date <= self.checkout_date:
                raise ValidationError(
                    {"due_date": "Due date must be after checkout date."}
                )

        if self.returned_date:
            if self.returned_date < self.checkout_date:
                raise ValidationError(
                    {"returned_date": "Return date cannot be before checkout date."}
                )
            if self.status != "RETURNED":
                raise ValidationError(
                    {"status": "Status must be RETURNED when returned_date is set."}
                )

        if not self._state.adding:
            try:
                original = Transaction.objects.get(pk=self.pk)
                if not self._is_valid_status_transition(original.status, self.status):
                    raise ValidationError(
                        {
                            "status": f"Invalid status transition from {original.status} to {self.status}."  # noqa
                        }
                    )
            except Transaction.DoesNotExist:
                pass

    def _is_valid_status_transition(self, old_status, new_status):
        """Check if status transition is allowed."""
        valid_transitions = {
            "PENDING": ["ISSUED", "RETURNED"],
            "ISSUED": ["RETURN_REQUESTED", "RETURNED"],
            "RETURN_REQUESTED": ["RETURNED", "ISSUED"],
            "RETURNED": [],
        }
        return new_status in valid_transitions.get(old_status, [])

    def save(self, *args, **kwargs):
        """
        Handle stock management atomically.
        """
        if not self.due_date and self.status == "ISSUED":
            self.due_date = timezone.now() + timedelta(days=14)

        with db_transaction.atomic():
            if not self.is_ebook:
                if not self._state.adding:
                    original = Transaction.objects.select_for_update().get(pk=self.pk)

                    # PENDING -> ISSUED
                    if original.status == "PENDING" and self.status == "ISSUED":
                        if not self.book.borrow_book():
                            raise ValidationError("Book is no longer available.")

                    # ISSUED/REQUESTED -> RETURNED
                    elif (
                        original.status in ["ISSUED", "RETURN_REQUESTED"]
                    ) and self.status == "RETURNED":
                        if not self.returned_date:
                            self.returned_date = timezone.now()
                        if not self.book.return_book():
                            raise ValidationError(
                                "Cannot return book - all copies already available."
                            )
                else:
                    if self.status == "ISSUED":
                        if not self.book.borrow_book():
                            raise ValidationError("Book not available for checkout.")

            super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if transaction is overdue."""
        if self.status == "RETURNED":
            return False
        return timezone.now() > self.due_date

    @property
    def days_overdue(self):
        """Calculate number of days overdue."""
        if not self.is_overdue:
            return 0
        delta = timezone.now() - self.due_date
        return delta.days

    @property
    def borrowing_period_days(self):
        """Calculate actual borrowing period in days."""
        end_date = self.returned_date or timezone.now()
        delta = end_date - self.checkout_date
        return delta.days

    def mark_as_returned(self):
        """Mark transaction as returned and update book stock."""
        if self.status == "RETURNED":
            return False

        self.status = "RETURNED"
        self.returned_date = timezone.now()
        self.save()
        return True

    def extend_due_date(self, days=7):
        """Extend the due date by specified days."""
        if self.status != "ISSUED":
            raise ValidationError("Can only extend due date for issued books.")

        self.due_date += timedelta(days=days)
        self.save()

    def __str__(self):
        return f"{self.user.email} - {self.book.title} ({self.get_status_display()})"

    def __repr__(self):
        return f"<Transaction: {self.pk} - {self.book.title} - {self.status}>"
