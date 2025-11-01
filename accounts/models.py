import uuid
import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser

from .utils import generate_user_code


# Create your models here.
class UserRoles(models.TextChoices):
    ADMIN = "admin", "Admin"
    LIBRARIAN = "librarian", "Librarian"
    STUDENT = "student", "Student"


class LibraryUser(AbstractUser):
    user_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    role = models.CharField(max_length=20, default=UserRoles.STUDENT, choices=UserRoles)
    date_of_birth = models.DateField(default=datetime.date(year=1900, month=1, day=1))
    user_code = models.CharField(unique=True, max_length=10)
    profile_image = models.ImageField(
        upload_to="profile_images/", default="profile_images/neutral.png"
    )

    def __str__(self):
        return self.username

    @property
    def age(self):
        today = datetime.date.today()
        dob = self.date_of_birth
        if dob == datetime.date(1900, 1, 1):
            return None
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @property
    def get_full_name(self):
        names = [self.first_name, self.last_name]
        cleaned = " ".join(name.title() for name in names if name)
        return cleaned if cleaned else self.username.title()

    def save(self, *args, **kwargs):
        if not self.user_code:
            self.user_code = generate_user_code(role=self.role)
        super().save(*args, **kwargs)
