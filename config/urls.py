from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path


# Блок 1. Главные URL-адреса проекта.
urlpatterns = [
    # Админ-панель Django:
    # /admin/
    path('admin/', admin.site.urls),

    # Подключаем URL-адреса приложения core.
    # Например, /register/
    path('', include('core.urls')),

    # Страница входа:
    # /login/
    # Используем готовое представление Django LoginView.
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='core/login.html'),
        name='login'
    ),

    # Страница выхода:
    # /logout/
    # Используем готовое представление Django LogoutView.
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),
]


# Блок 2. Подключение media-файлов в режиме разработки.
# Нужно, чтобы загруженные документы были доступны локально.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)