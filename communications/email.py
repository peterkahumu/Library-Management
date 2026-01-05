from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from book_circulation.models import Transaction


class LibraryEmailService:
    """
    Centralized service for sending library-related emails.
    """

    @staticmethod
    def _send(
        subject: str, 
        template_name: str, 
        context: dict[str, str], 
        recipient_email: str
    ):
        """Helper method to render and send emails"""
        message = render_to_string(f"emails/{template_name}", context)
        send_mail(
            subject=f"[Library] {subject}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False
        )

    @classmethod
    def send_borrow_request_confirmation(cls, transaction: Transaction):
        """Notify the student their request is pending library approval"""
        context = {
            "user": transaction.user.get_full_name(),
            "book_title": transaction.book.title,
        }

        cls._send("REQUEST RECEIVED", "borrow_request_pending.txt", context, transaction.user.email)
    
    @classmethod
    def send_book_issued_notification(cls, transaction: Transaction, download_link: str = None):
        """Notify the student that the book is officially in their possession"""
        context = {
            "user": transaction.user.get_full_name(),
            "book_title": transaction.book.title,
            "due_date": transaction.due_date.strftime("%Y-%m-%d"),
            "is_ebook": transaction.is_ebook,
            "download_link": download_link if download_link else ""
        }

        template = "book_issued_digital.txt" if transaction.is_ebook else "book_issued_physical.txt"
        cls._send("BOOK ISSUED", template, context, transaction.user.email)
    
    @classmethod
    def send_book_request_denied(cls, reason, transaction: Transaction):
        """Notify the student that the book request was denied"""

        context = {
            "user": transaction.user.get_full_name(),
            "book_title": transaction.book.title,
            "reason": reason
        }
        cls._send("BOOK REQUEST DENIED", "book_request_denied.txt", context, transaction.user.email)

    @classmethod
    def send_return_confirmation(cls, transaction):
        """Confirm that a return request has been submitted."""
        context = {
            "user": transaction.user.get_full_name(),
            "book_title": transaction.book.title,
        }
        cls._send("RETURN REQUESTED", "return_request_pending.txt", context, transaction.user.email)

    @classmethod
    def send_return_approval(cls, transaction):
        """Confirm that the librarian has processed the return."""
        context = {
            "user": transaction.user.get_full_name(),
            "book_title": transaction.book.title,
        }
        cls._send("RETURN CONFIRMED", "return_success.txt", context, transaction.user.email)

    @classmethod
    def send_return_denied(cls, reason: str, transaction: Transaction):
        """Notify the user returning of the book was denied"""
        context = {
            "user": transaction.user.get_full_name(),
            "book_title": transaction.book.title,
            "reason": reason
        }
        cls._send("RETURN REQUEST DENIED", "return_request_denied.txt", context, transaction.user.email)