import random
import string


def generate_user_code(role: str) -> str:
    """Generates a random user code for the user. It is unique all through."""
    prefix = role[:2].upper()

    from .models import LibraryUser

    while True:
        random_part = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        code = f"{prefix}{random_part}"

        if not LibraryUser.objects.filter(user_code=code).exists():
            return code
