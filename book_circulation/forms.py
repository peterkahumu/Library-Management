from django import forms
from django.core.exceptions import ValidationError


class BorrowForm(forms.Form):
    """
    Allow user to specify number of days to borrow book.
    Application validation to ensure number of days
    """

    duration_days = forms.IntegerField(
        min_value=1,
        max_value=14,
        initial=7,
        label="Borrowing Duration (Days)",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Number of days"}
        ),
    )

    def clean_duration_days(self):
        """
        Ensure number of days do not exceed 14
        :param self: class instance.
        """
        days = self.cleaned_data["duration_days"]
        if days > 14:
            raise ValidationError("Maximum number of days allowed is 14 days.")

        return days
