import uuid
from django.db import models
from django.conf import settings

from .constants import LANGUAGE_CHOICES, GENRE_CHOICES


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
    genre = models.ManyToManyField(Genre, related_name="books", blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")
    date_added = models.DateField(auto_now_add=True)
    total_copies = models.PositiveSmallIntegerField(default=1)
    copies_available = models.PositiveSmallIntegerField(default=1)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="books_added"
    )
    cover_image = models.ImageField(
        upload_to="books/", default="books/default_book.png"
    )

    def __str__(self):
        return self.title

    def borrow_book(self):
        if self.is_available:
            self.copies_available -= 1
            self.save(update_fields=["copies_available"])
            return True
        return False

    @property
    def is_available(self):
        return self.copies_available > 0

    def return_book(self):
        if self.copies_available < self.total_copies:
            self.copies_available += 1
            self.save(update_fields=["copies_available"])
            return True
        return False

    class Meta:
        ordering = ["-date_added"]
