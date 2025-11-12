from django.contrib import admin
from .models import Book, Genre


# Register your models here.
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "isbn",
        "author",
        "language",
        "total_copies",
        "copies_available",
        "date_added",
        "added_by",
    ]
    list_filter = [
        "genre",
        "language",
        "added_by",
    ]
    search_fields = ["title", "isbn", "author", "description"]


admin.site.register(Genre)
