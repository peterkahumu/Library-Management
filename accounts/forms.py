from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import LibraryUser
from django import forms


class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form to capture extra fields."""

    class Meta:
        model = LibraryUser
        fields = ["username", "first_name", "last_name", "email", "date_of_birth"]

        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}


class CustomUserChangeForm(UserChangeForm):
    """Custom user update form to capture additional fields."""

    class Meta:
        model = LibraryUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "profile_image",
        ]
