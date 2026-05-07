from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import LibraryUser, PersonalityProfile
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

class PersonalityProfileForm(forms.ModelForm):
    """Form to update Big Five personality traits."""
    
    class Meta:
        model = PersonalityProfile
        fields = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        widgets = {
            "openness": forms.NumberInput(attrs={"type": "range", "min": "0", "max": "1", "step": "0.01", "class": "form-range"}),
            "conscientiousness": forms.NumberInput(attrs={"type": "range", "min": "0", "max": "1", "step": "0.01", "class": "form-range"}),
            "extraversion": forms.NumberInput(attrs={"type": "range", "min": "0", "max": "1", "step": "0.01", "class": "form-range"}),
            "agreeableness": forms.NumberInput(attrs={"type": "range", "min": "0", "max": "1", "step": "0.01", "class": "form-range"}),
            "neuroticism": forms.NumberInput(attrs={"type": "range", "min": "0", "max": "1", "step": "0.01", "class": "form-range"}),
        }
