# Accounts App

The `accounts` app defines the custom user model and user registration flow.

## Responsibilities

- Custom `LibraryUser` model with UUID primary key.
- Role management (`admin`, `librarian`, `student`).
- Auto-generated user code.
- Registration view and form integration.

## Key Files

- `models.py`: `LibraryUser`, `LibraryUserManager`, role definitions.
- `views.py`: `RegisterUserView`.
- `urls.py`: `accounts/register/` route.
- `management/commands/seed_superuser.py`: optional seeded admin creation from env vars.

## Notes

- `AUTH_USER_MODEL` is set to `accounts.LibraryUser`.
- Admin role users are automatically made staff/superuser during save.
