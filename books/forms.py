from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
import datetime
import re
from .models import Book
from .google_books import GoogleBooksAPI


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "description",
            "isbn",
            "author",
            "publication_date",
            "edition",
            "genre",
            "language",
            "total_copies",
            "copies_available",
            "cover_image",
            "publisher",
            "format",
            "dimensions",
            "weight",
            "dewey_decimal",
        ]

        widgets = {
            "publication_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "genre": forms.CheckboxSelectMultiple(),
        }

    def clean_isbn(self):
        isbn = self.cleaned_data.get("isbn")
        if not isbn.isdigit():
            raise ValidationError("ISBN must be numeric.")
        if len(isbn) not in [10, 13]:
            raise ValidationError("ISBN must be 10 or 13 digits.")
        return isbn

    def clean_publication_date(self):
        today = datetime.date.today()
        publication_date = self.cleaned_data.get("publication_date")

        if publication_date and publication_date > today:
            raise ValidationError("The publication date cannot be in the future.")
        return publication_date

    def clean_genre(self):
        genres = self.cleaned_data.get("genre")
        if not genres:
            raise ValidationError("A book must be in at least one genre.")
        return genres


class GoogleBookImportForm(forms.ModelForm):
    """
    Form for importing and customizing books from Google Books API.

    This form allows admins/librarians to customize book details
    before adding them to the library from Google Books.
    """

    # Hidden field to store the Google Books volume ID
    google_volume_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Book
        fields = [
            "title",
            "description",
            "isbn",
            "author",
            "publication_date",
            "edition",
            "genre",
            "language",
            "total_copies",
            "copies_available",
            "publisher",
            "format",
        ]

        widgets = {
            "publication_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "genre": forms.CheckboxSelectMultiple(),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "author": forms.TextInput(attrs={"class": "form-control"}),
            "isbn": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with optional Google Books data."""
        google_data = kwargs.pop("google_data", None)
        super().__init__(*args, **kwargs)

        # Make certain fields required
        self.fields["total_copies"].initial = 1
        self.fields["copies_available"].initial = 1

        # Pre-populate from Google Books data if provided
        if google_data:
            volume_info = google_data.get("volumeInfo", {})

            # Store the volume ID
            self.initial["google_volume_id"] = google_data.get("id", "")

            # Pre-fill fields
            if "title" in volume_info:
                self.initial["title"] = volume_info["title"]

            if "description" in volume_info:
                description = volume_info["description"]
                # Convert logic breaks to newlines
                description = re.sub(
                    r"<br\s*/?>", "\n", description, flags=re.IGNORECASE
                )
                description = re.sub(r"</p>", "\n\n", description, flags=re.IGNORECASE)
                # Strip remaining tags and enforce model field max_length
                cleaned_description = strip_tags(description).strip()
                try:
                    desc_field = Book._meta.get_field("description")
                    max_length = getattr(desc_field, "max_length", None)
                except Exception:
                    max_length = None
                if max_length is not None and len(cleaned_description) > max_length:
                    cleaned_description = cleaned_description[:max_length]
                self.initial["description"] = cleaned_description

            # Extract authors
            authors = volume_info.get("authors", [])
            if authors:
                self.initial["author"] = ", ".join(authors)

            # Extract ISBN
            isbn = GoogleBooksAPI.extract_isbn(volume_info)
            if isbn:
                self.initial["isbn"] = isbn

            # Publication date
            pub_date = GoogleBooksAPI.extract_publication_date(volume_info)
            if pub_date:
                self.initial["publication_date"] = pub_date

            # Publisher
            if "publisher" in volume_info:
                self.initial["publisher"] = volume_info["publisher"]

            # Language (convert from Google's format to our choices)
            language = volume_info.get("language", "en")
            self.initial["language"] = language[:2].lower()  # Use first 2 chars

    def clean_isbn(self):
        """Validate ISBN format and uniqueness."""
        isbn = self.cleaned_data.get("isbn")

        if not isbn:
            raise ValidationError("ISBN is required for importing books.")

        if not isbn.replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("ISBN must contain only digits.")

        # Remove formatting
        isbn_clean = isbn.replace("-", "").replace(" ", "")

        if len(isbn_clean) not in [10, 13]:
            raise ValidationError("ISBN must be 10 or 13 digits.")

        # Check for duplicate ISBN (excluding current instance if updating)
        existing = Book.objects.filter(isbn=isbn_clean)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError(
                f"A book with ISBN {isbn_clean} already exists in the library. "
                "Please check the catalogue before importing."
            )

        return isbn_clean

    def clean_publication_date(self):
        """Validate publication date is not in the future."""
        today = datetime.date.today()
        publication_date = self.cleaned_data.get("publication_date")

        if publication_date and publication_date > today:
            raise ValidationError("The publication date cannot be in the future.")
        return publication_date

    def clean_genre(self):
        """Ensure at least one genre is selected."""
        genres = self.cleaned_data.get("genre")
        if not genres:
            raise ValidationError("Please select at least one genre for this book.")
        return genres

    def clean(self):
        """Validate copies_available doesn't exceed total_copies."""
        cleaned_data = super().clean()
        total_copies = cleaned_data.get("total_copies")
        copies_available = cleaned_data.get("copies_available")

        if total_copies and copies_available:
            if copies_available > total_copies:
                raise ValidationError("Available copies cannot exceed total copies.")

        return cleaned_data
