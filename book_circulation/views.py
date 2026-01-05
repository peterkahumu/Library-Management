from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.views.generic import FormView, ListView
from django.views import View

from books.models import Book
from accounts.models import UserRoles
from .models import Transaction
from .forms import BorrowForm

# --- Student Views ---


def is_librarian_or_staff(user):
    return user.is_authenticated and user.role in [UserRoles.ADMIN, UserRoles.LIBRARIAN]


class BorrowBookView(LoginRequiredMixin, FormView):
    template_name = "circulation/borrow_confirm.html"
    form_class = BorrowForm
    success_url = reverse_lazy("my_books")

    def dispatch(self, request, *args, **kwargs):
        """
        Run checks before loading the form.
        If the user already has the book, redirect them immediately.
        """
        self.book = get_object_or_404(Book, pk=kwargs["book_id"])

        # Check for active transactions
        if Transaction.objects.filter(
            user=request.user,
            book=self.book,
            status__in=["ISSUED", "PENDING", "RETURN_REQUESTED"],
        ).exists():
            messages.warning(
                request, "You already have an active request or loan for this book."
            )
            return redirect("book_detail", pk=self.book.pk)
        if not self.book.is_available:
            messages.error(request, "Book out of stock at the moment. Try again later.")
            return redirect("book_detail", pk=self.book.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Inject the book object into the template context."""
        context = super().get_context_data(**kwargs)
        context["book"] = self.book
        return context

    def form_valid(self, form):
        """Handle the business logic once the form is submitted and valid."""
        # Use .get() with a default or safety net as discussed
        duration = form.cleaned_data.get("duration_days") or 7
        due_date = timezone.now() + timedelta(days=duration)

        try:
            if self.book.is_digital:
                # E-Book Flow
                Transaction.objects.create(
                    user=self.request.user,
                    book=self.book,
                    due_date=due_date,
                    status="DOWNLOADED",
                    is_ebook=True,
                )
                messages.success(self.request, "E-Book downloaded successfully!")
            else:
                # Physical Book Flow
                if not self.book.is_available:
                    messages.error(self.request, "This book is currently out of stock.")
                    return redirect("book_detail", pk=self.book.pk)

                Transaction.objects.create(
                    user=self.request.user,
                    book=self.book,
                    due_date=due_date,
                    status="PENDING",
                    is_ebook=False,
                )
                messages.success(
                    self.request,
                    "Request submitted. Please visit the librarian to complete checkout.",  # noqa
                )
        except Exception as e:
            messages.error(self.request, f"An error occurred: {e}")
            return self.form_invalid(form)

        return super().form_valid(form)


class MyBooksListView(LoginRequiredMixin, ListView):
    """
    List all the books that the user has borrowed
    Includes all books, whether issued or not.
    """

    model = Transaction
    template_name = "circulation/my_books.html"
    context_object_name = "transactions"
    paginate_by = 10

    def get_queryset(self):
        """Filter transactions to show only the current user's history."""
        return (
            Transaction.objects.filter(user=self.request.user)
            .select_related("book")
            .order_by("-checkout_date")
        )


class RequestReturnView(LoginRequiredMixin, View):
    """
    Allow student to reqeust a return for an issued book."""

    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

        if transaction.status == "ISSUED":
            transaction.status = "RETURN_REQUESTED"
            try:
                transaction.save()
                messages.success(
                    request,
                    "Return request submitted. "
                    "Please hand in the physical copy to the librarian for approval.",
                )
            except Exception as e:
                messages.error(request, f"Error submitting request: {e}")
        else:
            messages.error(
                request,
                f"Books with status {transaction.get_status_display()} cannot perform this operation",  # noqa
            )

        return redirect("my_books")


# --- Librarian Views ---
class LibrarianBorrowRequestsView(UserPassesTestMixin, ListView):
    model = Transaction
    template_name = "circulation/librarian_borrow_requests.html"
    context_object_name = "borrow_requests"
    paginate_by = 10

    def test_func(self):
        return is_librarian_or_staff(self.request.user)

    def get_queryset(self):
        return (
            Transaction.objects.filter(status="PENDING")
            .select_related("book", "user")
            .order_by("checkout_date")
        )


class LibrarianReturnRequestsView(UserPassesTestMixin, ListView):
    model = Transaction
    template_name = "circulation/librarian_return_requests.html"
    context_object_name = "return_requests"
    paginate_by = 10

    def test_func(self):
        return is_librarian_or_staff(self.request.user)

    def get_queryset(self):
        return (
            Transaction.objects.filter(status="RETURN_REQUESTED")
            .select_related("book", "user")
            .order_by("returned_date")
        )


class RejectBorrowView(UserPassesTestMixin, View):
    """Reject a borrow request."""

    def test_func(self):
        return is_librarian_or_staff(self.request.user)

    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk)
        if transaction.status == "PENDING":
            try:
                transaction.delete()
                messages.warning(
                    request,
                    f"Borrow request for {transaction.book.title} rejected/cancelled.",
                )
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return redirect("librarian_borrow_requests")


class RejectReturnView(UserPassesTestMixin, View):
    """Reject a return request (e.g., book damaged or not received)."""

    def test_func(self):
        return is_librarian_or_staff(self.request.user)

    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk)
        if transaction.status == "RETURN_REQUESTED":
            try:
                # Revert to ISSUED status so it stays as borrowed
                transaction.status = "ISSUED"
                transaction.save()
                messages.warning(
                    request, "Return request rejected. Book marked as still ISSUED."
                )
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return redirect("librarian_return_requests")


class ApproveBorrowView(UserPassesTestMixin, View):
    """Approve a borrow request."""

    def test_func(self):
        return is_librarian_or_staff(self.request.user)

    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk)
        if transaction.status == "PENDING":
            try:
                transaction.status = "ISSUED"
                transaction.save()
                messages.success(
                    request, f"Book issued to {transaction.user.get_full_name()}"
                )
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return redirect("librarian_borrow_requests")


class ApproveReturnView(UserPassesTestMixin, View):
    """
    Approve a return request for a book
    """

    def test_func(self):
        return is_librarian_or_staff(self.request.user)

    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk)
        try:
            if transaction.mark_as_returned():
                messages.success(
                    request, f"{transaction.book.title} returned successfully."
                )
            else:
                messages.warning(request, "Book is already returned.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect("librarian_return_requests")
