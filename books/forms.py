from django import forms
from django.core.exceptions import ValidationError
import datetime
from .models import Book


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
            "format": forms.TextInput(attrs={"placeholder": "ebook, hardcopy,..."}),
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
