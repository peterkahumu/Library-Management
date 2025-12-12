from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.views.generic import FormView, ListView

from books.models import Book
from .models import Transaction
from .forms import BorrowForm

# --- Student Views ---


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
            user=request.user, book=self.book, status__in=["ISSUED", "PENDING"]
        ).exists():
            messages.warning(
                request, "You already have an active request or loan for this book."
            )
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
                    status="ISSUED",
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
            # Catch any unexpected model validation errors
            messages.error(self.request, f"An error occurred: {e}")
            return self.form_invalid(form)

        return super().form_valid(form)


class MyBooksListView(LoginRequiredMixin, ListView):
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


# --- Librarian Views ---


class LibrarianDashboardView(UserPassesTestMixin, ListView):
    model = Transaction
    template_name = "circulation/librarian_dashboard.html"
    context_object_name = "transactions"

    def test_func(self):
        """Ensure only staff/librarians can access this view."""
        return self.request.user.is_staff or self.request.user.role == "librarian"

    def get_queryset(self):
        """Show only pending requests."""
        return Transaction.objects.filter(status="PENDING").select_related(
            "book", "user"
        )


def is_librarian_or_staff(user):
    return user.is_authenticated and (user.is_staff or user.role == "librarian")


@user_passes_test(is_librarian_or_staff)
def approve_borrow(request, transaction_id):
    txn = get_object_or_404(Transaction, pk=transaction_id)
    try:
        txn.status = "ISSUED"
        txn.save()  # Triggers model logic to decrement stock
        messages.success(request, f"Book issued to {txn.user.username}.")
    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect("librarian_dashboard")


@user_passes_test(is_librarian_or_staff)
def return_book_action(request, transaction_id):
    txn = get_object_or_404(Transaction, pk=transaction_id)
    try:
        txn.mark_as_returned()
        messages.success(request, "Book returned successfully.")
    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect("librarian_dashboard")
