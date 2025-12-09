import uuid
from datetime import date
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
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

    def test_get_full_name(self):
        """Make sure the name is correct and falls back to username successfully."""
        control = User.objects.create_user(
            username="controluser",
            first_name="user  ",
            password="control",
            email="controluser@control.com",
        )
        control1 = User.objects.create_user(
            username="controluser1",
            last_name="user1  ",
            password="control",
            email="controluser1@controluser.com",
        )
        self.assertEqual(self.user.get_full_name(), "Testuser")
        self.assertEqual(self.super_user.get_full_name(), "Admin User")
        self.assertEqual(control.get_full_name(), "User")
        self.assertEqual(control1.get_full_name(), "User1")

    def test_user_id_unique(self):
        """Test to make sure that each user id is unique."""
        control = User.objects.create_user(
            username="control", password="control", email="controluser@control.com"
        )

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

    def test_uuid_uniqueness(self):
        """Each user must have a unique UUID."""
        ids = [
            User.objects.create_user(
                username=f"user{i}", email=f"user{i}@a.com", password="123"
            ).user_id
            for i in range(5)
        ]
        self.assertEqual(len(ids), len(set(ids)))

    def test_age(self):
        """Make sure that age is functioning as expected and default value set."""
        dob = self.user.date_of_birth
        dob1 = self.super_user.date_of_birth
        today = timezone.now().date()

        self.assertIsNone(dob)
        self.assertIsNone(self.user.age)

        expected_age = (
            today.year - dob1.year - ((today.month, today.day) < (dob1.month, dob1.day))
        )
        self.assertEqual(self.super_user.age, expected_age)

    def test_role(self):
        """Test role to ensure it behaves as expected."""
        control = User.objects.create_user(
            username="control",
            password="control",
            role="admin",
            email="controluser@control.com",
        )
        self.assertEqual(self.user.role, "student")
        self.assertEqual(self.super_user.role, "admin")
        self.assertEqual(control.role, "admin")
        self.assertTrue(control.is_staff)
        self.assertTrue(control.is_superuser)

    def test_user_code(self):
        """Test code exists and is unique."""
        control = User.objects.create_user(
            username="username",
            password="password",
            role="librarian",
            email="controluser@control.com",
        )
        control1 = User.objects.create_user(
            username="username2",
            password="password",
            role="admin",
            email="controluser@control1.com",
        )

        self.assertEqual(self.user.user_code[:2], "ST")
        self.assertEqual(control.user_code[:2], "LI")
        self.assertEqual(control1.user_code[:2], "AD")
        self.assertEqual(len(self.user.user_code), 8)
        self.assertEqual(len(control.user_code), 8)
        self.assertEqual(len(control1.user_code), 8)

        users = User.objects.filter(user_code=self.user.user_code)
        self.assertEqual(users.count(), 1)

    def test_admin_role_sets_permissions(self):
        """Ensure admin role always enforces is_staff and is_superuser."""
        admin = User.objects.create_user(
            username="adminuser", email="ad@a.com", password="123", role="admin"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class RegisterUserTests(TestCase):
    """Test the Register User endpoint."""

    def setUp(self):
        self.url = self.client.get(reverse("register"))
        self.url_hardcoded = self.client.get("/accounts/register/")
        self.user_register = self.client.post(
            reverse("register"),
            {
                "username": "testuser",
                "email": "testuser@test.com",
                "password1": "@Test12345",
                "password2": "@Test12345",
            },
        )

    def test_urls_status_code(self):
        """Ensure that the expected status code is returned."""
        self.assertEqual(self.url.status_code, 200)
        self.assertEqual(self.url_hardcoded.status_code, 200)
        self.assertEqual(self.user_register.status_code, 302)

    def test_urls_templates(self):
        """Correct templates are being used and contains expected content."""
        self.assertTemplateUsed(self.url, "registration/register.html")
        self.assertTemplateUsed(self.url_hardcoded, "registration/register.html")

        self.assertContains(self.url, "Create an Account")
        self.assertContains(self.url_hardcoded, "Create an Account")

    def test_redirect_after_registration(self):
        """After registration, the user is redirected to the login page."""
        self.assertRedirects(self.user_register, reverse("login"))

    def test_required_fields(self):
        """Ensure username, email, and password are required."""
        control = self.client.post(
            reverse("register"),
            {
                "first_name": "controltest",
                "password2": "TestPassword",
            },
        )

        self.assertEqual(control.status_code, 200)
        self.assertContains(control, "This field is required", count=3)

        # check the specific errors.
        form = control.context["form"]
        self.assertIn("username", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("password1", form.errors)

    def test_duplicate_user_registration(self):
        """Only the first post should be successful. The second should fail."""
        user = self.client.post(
            reverse("register"),
            {
                "username": "testuser",
                "email": "testuser@test.com",
                "password1": "@Test12345",
                "password2": "@Test12345",
            },
        )

        self.assertEqual(user.status_code, 200)

        form = user.context["form"]
        self.assertIn("username", form.errors)
        self.assertIn("email", form.errors)

        # Error messages
        self.assertIn(
            "A user with that username already exists.", form.errors["username"]
        )
        self.assertIn("User with this Email already exists.", form.errors["email"])

    def test_invalid_date_format(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "baduser",
                "email": "baduser@test.com",
                "password1": "@Test12345",
                "password2": "@Test12345",
                "date_of_birth": "31-12-2000",  # Wrong format
            },
        )
        self.assertContains(response, "Enter a valid date.")


class UserCacheInvalidationTests(TestCase):
    """Test cache invalidation signals for user stats."""

    def setUp(self):
        """Clear cache before each test."""
        from django.core.cache import cache

        cache.clear()

    def test_cache_invalidated_on_user_creation(self):
        """Creating a user should clear stats:total_users cache."""
        from django.core.cache import cache

        cache.set("stats:total_users", 100)
        self.assertEqual(cache.get("stats:total_users"), 100)

        User.objects.create_user(
            username="newuser",
            email="new@example.com",
            password="testpass123",
            first_name="New",
            last_name="User",
        )

        self.assertIsNone(cache.get("stats:total_users"))

    def test_cache_invalidated_on_user_update(self):
        """Updating a user should clear stats:total_users cache."""
        from django.core.cache import cache

        user = User.objects.create_user(
            username="updateuser",
            email="update@example.com",
            password="testpass123",
            first_name="Update",
            last_name="User",
        )

        cache.set("stats:total_users", 100)
        self.assertEqual(cache.get("stats:total_users"), 100)

        user.first_name = "Updated"
        user.save()

        self.assertIsNone(cache.get("stats:total_users"))

    def test_cache_invalidated_on_user_deletion(self):
        """Deleting a user should clear stats:total_users cache."""
        from django.core.cache import cache

        user = User.objects.create_user(
            username="deleteuser",
            email="delete@example.com",
            password="testpass123",
            first_name="Delete",
            last_name="User",
        )

        cache.set("stats:total_users", 100)
        self.assertEqual(cache.get("stats:total_users"), 100)

        user.delete()

        self.assertIsNone(cache.get("stats:total_users"))

    def test_cache_not_affected_by_other_operations(self):
        """Cache should only be invalidated by user save/delete, not reads."""
        from django.core.cache import cache

        User.objects.create_user(
            username="readuser", email="read@example.com", password="testpass123"
        )

        cache.set("stats:total_users", 100)

        # Reading user shouldn't invalidate cache
        User.objects.get(username="readuser")
        self.assertEqual(cache.get("stats:total_users"), 100)

        # Filtering shouldn't invalidate cache
        User.objects.filter(is_active=True)
        self.assertEqual(cache.get("stats:total_users"), 100)
