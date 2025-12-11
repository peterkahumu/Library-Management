import uuid
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import F

from .constants import LANGUAGE_CHOICES, GENRE_CHOICES, FORMAT_CHOICES


# Create your models here.
class Genre(models.Model):
    """
    Represents a literary genre or category that can be assigned to one or more books.
    """

    name = models.CharField(max_length=50, choices=GENRE_CHOICES, unique=True)

    def __str__(self):
        return dict(self._meta.get_field("name").choices).get(self.name, self.name)

    class Meta:
        ordering = ["name"]


class Book(models.Model):
    """Book model"""

    book_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    description = models.TextField()
    isbn = models.CharField(unique=True, max_length=13)
    author = models.CharField(max_length=200)
    publication_date = models.DateField()  # cannot be null, user must provide.
    edition = models.CharField(max_length=10, blank=True, null=True)
    genre = models.ManyToManyField(Genre, related_name="books")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")
    date_added = models.DateTimeField(auto_now_add=True)
    total_copies = models.PositiveSmallIntegerField(default=1)
    copies_available = models.PositiveSmallIntegerField(default=1)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="books_added"
    )
    cover_image = models.ImageField(
        upload_to="books/", default="books/default_book.png"
    )
    featured = models.BooleanField(default=False)

    # other fields
    publisher = models.CharField(max_length=100, blank=True, null=True)
    format = models.CharField(max_length=50, choices=FORMAT_CHOICES, default="HARDCOPY")
    dimensions = models.CharField(
        max_length=50, blank=True, null=True
    )  # l x w x h in inches
    weight = models.FloatField(blank=True, null=True)
    dewey_decimal = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.copies_available > 0

    @property
    def is_digital(self):
        """
        Classify object as digital or not.

        :param self: Object instance.
        """

        return self.format in ["EBOOK", "AUDIOBOOK"]

    def borrow_book(self):
        """
        Atomic decrement of books
        """
        updated = Book.objects.filter(
            book_id=self.book_id, copies_available__gt=0
        ).update(copies_available=F("copies_available") - 1)
        if updated:
            self.refresh_from_db()
            return True
        return False

    def return_book(self):
        """
        Atomic increment of books. Does not exceed total_copies
        """
        updated = Book.objects.filter(
            book_id=self.book_id, copies_available__lt=F("total_copies")
        ).update(copies_available=F("copies_available") + 1)

        if updated:
            self.refresh_from_db()
            return True
        return False

    def get_absolute_url(self):
        return reverse("book_detail", kwargs={"pk": self.book_id})

    def clean(self):
        """
        Enforce the following rules:
        1. total_copies >=0
        2. copies available >=0
        3. copies available <= total copies.
        4. An attempt to modify the total copies
        such that new total copies < copies available raises an error.
        """

        if self.total_copies < 0:
            raise ValidationError(
                {"total_copies": "Total copies must be greater than 0"}
            )

        if self.copies_available < 0:
            raise ValidationError(
                {"copies_available": "Copies available cannot be negative."}
            )

        if self.copies_available > self.total_copies:
            raise ValidationError(
                {"copies_available": "Copies available cannot exceed total copies."}
            )

        # for existing books
        if not self._state.adding:
            old_available = self.__class__.objects.get(pk=self.pk).copies_available

            if self.total_copies < old_available:
                raise ValidationError(
                    {
                        "total_copies": "Total copies cannot be "
                        "set below current available copies. "
                        "Adjust the available copies first."
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["-date_added"]
