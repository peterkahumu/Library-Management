from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import LibraryUser


class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form to capture extra fields."""

    class Meta:
        model = LibraryUser
        fields = ["username", "first_name", "last_name", "email", "date_of_birth"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove default values and add placeholders
        self.fields["date_of_birth"].widget.attrs.update({"placeholder": "MM/DD/YYYY"})


class CustomUserChangeForm(UserChangeForm):
    """Custom user update form to capture additional fields."""

    class Meta:
        model = LibraryUser
        fields = ["username", "first_name", "last_name", "email", "date_of_birth"]
