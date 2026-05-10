from django.urls import path
from . import views

# Блок 1. URL-адреса приложения core.
# Здесь мы определяем URL-адреса, которые будут обрабатывать функции из core/views.py.
urlpatterns = [
    # URL-адрес для страницы регистрации:
    # /register/
    path("register/",views.register_view, name = "register" )
]
