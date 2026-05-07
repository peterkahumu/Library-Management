from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import CustomUserCreationForm


class RegisterUserView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")

from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import PersonalityProfile
from .forms import PersonalityProfileForm

class PersonalityProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = PersonalityProfile
    form_class = PersonalityProfileForm
    template_name = "accounts/personality_profile_form.html"
    success_url = reverse_lazy("home")  # Redirect to home or dashboard after update

    def get_object(self, queryset=None):
        profile, created = PersonalityProfile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, "Your personality profile has been updated.")
        return super().form_valid(form)
