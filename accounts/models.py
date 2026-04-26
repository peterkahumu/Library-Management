import uuid
import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

from .utils import generate_user_code


# Create your models here.
class UserRoles(models.TextChoices):
    ADMIN = "admin", "Admin"
    LIBRARIAN = "librarian", "Librarian"
    STUDENT = "student", "Student"


class LibraryUserManager(BaseUserManager):
    """
    Custom manager for LibraryUser model.
    Handles user creation logic for both regular and superuser accounts.
    Ensures roles, permissions, and credentials are set appropriately.
    """

    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Create and return a regular user with the given username, email, and password.

        Args:
            username (str): The username for the user.
            email (str): The user's email address.
            password (str, optional): The user's password.
            **extra_fields: Additional fields for the user model.

        Raises:
            ValueError: If the username is not provided.

        Returns:
            LibraryUser: The created user instance.
        """
        if not username:
            raise ValueError("Username is required.")
        if not email:
            raise ValueError("Email is required.")
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and return a superuser with admin role and full permissions.

        Automatically sets:
            - role = admin
            - is_staff = True
            - is_superuser = True
        """
        extra_fields.setdefault("role", UserRoles.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)


class LibraryUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Features:
        - UUID primary key (user_id)
        - Role-based access (Admin, Librarian, Student)
        - Auto-generated unique user code
        - Optional profile image
        - Computed fields for full name and age
    """

    user_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    role = models.CharField(
        max_length=20, default=UserRoles.STUDENT, choices=UserRoles.choices
    )
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    user_code = models.CharField(unique=True, max_length=10)
    profile_image = models.ImageField(
        upload_to="profile_images/", default="profile_images/neutral.png"
    )

    def __str__(self):
        return self.username

    @property
    def age(self):
        """Return the user's age in years, or None if date_of_birth is unset."""
        today = datetime.date.today()
        dob = self.date_of_birth
        if not dob:
            return None
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def get_full_name(self):
        """
        Return the user's full name (first + last),
        falling back to the username if both are missing.
        """
        names = [self.first_name, self.last_name]
        cleaned = " ".join(name.title() for name in names if name)
        return cleaned.strip() if cleaned else self.username.title().strip()

    def save(self, *args, **kwargs):
        """
        Override default save to auto-generate user_code and set admin privileges.

        - Generates user_code if missing.
        - Ensures all admins are superusers with staff access.
        """
        if not self.user_code:
            self.user_code = generate_user_code(role=self.role)

        # all admins are super users.
        if self.role == UserRoles.ADMIN:
            self.is_staff = True
            self.is_superuser = True

        super().save(*args, **kwargs)

    objects = LibraryUserManager()
