from django.urls import path

from .api_views import RegisterAPIView


# Блок 1. API-маршруты приложения core.
urlpatterns = [
    # API регистрации:
    # /api/register/
    path('register/', RegisterAPIView.as_view(), name='api_register'),
]