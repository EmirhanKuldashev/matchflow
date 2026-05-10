from django.urls import path

from .api_views import LoginAPIView, ProfileAPIView, RegisterAPIView


# Блок 1. API-маршруты приложения core.
urlpatterns = [
    # API регистрации:
    # /api/register/
    path('register/', RegisterAPIView.as_view(), name='api_register'),

    # API входа по email:
    # /api/login/
    path('login/', LoginAPIView.as_view(), name='api_login'),

    # API личного кабинета:
    # /api/profile/
    path('profile/', ProfileAPIView.as_view(), name='api_profile'),
]