from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import RegisterForm


# Блок 1. Представление страницы регистрации.
# Эта функция показывает форму регистрации и обрабатывает её отправку.
def register_view(request):
    # Блок 2. Если пользователь отправил форму.
    if request.method == 'POST':
        # Получаем данные, которые пользователь ввёл в форму.
        form = RegisterForm(request.POST)

        # Проверяем, что данные корректные:
        # пароли совпадают, username не занят, обязательные поля заполнены.
        if form.is_valid():
            # Сохраняем пользователя.
            # Внутри form.save() создаются User и Profile.
            form.save()

            # Показываем сообщение об успешной регистрации.
            messages.success(
                request,
                'Регистрация прошла успешно. Теперь вы можете войти в систему.'
            )

            # После регистрации отправляем пользователя на страницу входа.
            return redirect('login')

    # Блок 3. Если пользователь просто открыл страницу регистрации.
    else:
        # Создаём пустую форму.
        form = RegisterForm()

    # Блок 4. Отображаем HTML-страницу регистрации.
    return render(request, 'core/register.html', {'form': form})