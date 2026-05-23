from django.urls import path
from .views import RegisterUserView, PersonalityProfileUpdateView

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path(
        "profile/update/", PersonalityProfileUpdateView.as_view(), name="update_profile"
    ),
]
