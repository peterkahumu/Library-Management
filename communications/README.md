# Communications Module

This module contains email delivery logic for library workflows.

## File

- `email.py`: `LibraryEmailService`

## Responsibilities

- Render email templates from `templates/emails/`.
- Send lifecycle notifications (borrow request, issue, return, denial events).

## Configuration

- Uses Django `send_mail`.
- Sender value is read from `settings.DEFAULT_FROM_EMAIL`.
- Default backend in development is console email backend.
