from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import CustomUserCreationForm


class RegisterUserView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")
