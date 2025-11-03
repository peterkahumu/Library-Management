from django import forms

from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "isbn",
            "description",
            "publication_date",
            "edition",
            "genre",
            "language",
            "total_copies",
            "copies_available",
            "cover_image",
        ]
