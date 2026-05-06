from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import LibraryUser, PersonalityProfile
from .forms import CustomUserChangeForm, CustomUserCreationForm


# Register your models here.
@admin.register(LibraryUser)
class CustomerUserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "first_name",
        "last_name",
        "role",
        "age",
    ]
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("role", "date_of_birth", "user_code", "profile_image")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("role", "date_of_birth")}),
    )

@admin.register(PersonalityProfile)
class PersonalityProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
    ]