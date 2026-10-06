from django.urls import path, include
from .views import MeView

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
    path("api/me/", MeView.as_view()),
]