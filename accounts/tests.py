import uuid
from datetime import date
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model

# Create your tests here.
User = get_user_model()


class UserManagerTests(TestCase):
    """Test the user model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@user.com", password="Test1234"
        )

        dob = date(2025, 11, 1)
        self.super_user = User.objects.create_superuser(
            username="superuser",
            first_name="Admin",
            last_name="User",
            email="superuser@superuser.com",
            password="Superuser1234",
            date_of_birth=dob,
        )

    def test_normal_user(self):
        """Test that the user properties are as expected."""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(str(self.user), "testuser")
        self.assertEqual(self.user.email, "test@user.com")
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_super_user(self):
        """Test the unique attributes of a super user."""
        self.assertTrue(self.super_user.is_active)
        self.assertTrue(self.super_user.is_staff)
        self.assertTrue(self.super_user.is_superuser)

    def test_password_hashed(self):
        """Make sure that the password is not stored in plain text."""
        self.assertIsNotNone(self.user.password)
        self.assertIsNotNone(self.super_user.password)
        self.assertNotEqual(self.user.password, "Test1234")
        self.assertNotEqual(self.super_user.password, "Test1234")

    def test_full_name(self):
        """Make sure the name is correct and falls back to username successfully."""
        control = User.objects.create_user(
            username="controluser", first_name="user  ", password="control"
        )
        control1 = User.objects.create_user(
            username="controluser1", last_name="user1  ", password="control"
        )
        self.assertEqual(self.user.full_name, "Testuser")
        self.assertEqual(self.super_user.full_name, "Admin User")
        self.assertEqual(control.full_name, "User")
        self.assertEqual(control1.full_name, "User1")

    def test_user_id_unique(self):
        """Test to make sure that each user id is unique."""
        control = User.objects.create_user(username="control", password="control")

        self.assertIsNotNone(control.user_id)
        self.assertIsNotNone(self.user.user_id)
        self.assertIsNotNone(self.super_user.user_id)

        result = User.objects.filter(pk=self.user.user_id)
        result1 = User.objects.filter(pk=self.super_user.user_id)
        result2 = User.objects.filter(pk=control.user_id)

        self.assertEqual(result.count(), 1)
        self.assertEqual(result1.count(), 1)
        self.assertEqual(result2.count(), 1)

    def test_uuid_field_correct_instance(self):
        """Ensure that the user_id is an instance of UUID field"""
        self.assertIsInstance(self.user.pk, uuid.UUID)

    def test_age(self):
        """Make sure that age is functioning as expected and default value set."""
        dob = self.user.date_of_birth
        dob1 = self.super_user.date_of_birth
        today = timezone.now().date()

        self.assertIsNotNone(dob)
        self.assertIsNone(self.user.age)
        self.assertEqual(dob, date(1900, 1, 1))

        expected_age = (
            dob1.year - today.year - ((today.month, today.day) < (dob1.month, dob1.day))
        )
        self.assertEqual(self.super_user.age, expected_age)

    def test_role(self):
        """Test role to ensure it behaves as expected."""
        control = User.objects.create_user(
            username="control", password="control", role="admin"
        )
        self.assertEqual(self.user.role, "student")
        self.assertEqual(self.super_user.role, "student")
        self.assertTrue(control.role, "admin")
        self.assertTrue(control.is_staff)
        self.assertTrue(control.is_superuser)

    def test_user_code(self):
        """Test code exists and is unique."""
        control = User.objects.create_user(
            username="username", password="password", role="librarian"
        )
        control1 = User.objects.create_user(
            username="username2", password="password", role="admin"
        )

        self.assertEqual(self.user.user_code[:2], "ST")
        self.assertEqual(control.user_code[:2], "LI")
        self.assertEqual(control1.user_code[:2], "AD")
        self.assertEqual(len(self.user.user_code), 8)
        self.assertEqual(len(control.user_code), 8)
        self.assertEqual(len(control1.user_code), 8)

        users = User.objects.filter(user_code=self.user.user_code)
        self.assertEqual(users.count(), 1)


class RegisterUserTests(TestCase):
    """Test the Register User endpoint."""

    pass
