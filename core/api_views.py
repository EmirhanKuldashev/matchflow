from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserProfileSerializer


# Блок 1. API регистрации пользователя.
# Этот класс обрабатывает POST-запрос на /api/register/.
class RegisterAPIView(APIView):
    # Блок 2. Метод POST.
    # Он вызывается, когда React или другой клиент отправляет данные регистрации.
    def post(self, request):
        # Передаём данные запроса в сериализатор.
        serializer = RegisterSerializer(data=request.data)

        # Проверяем данные.
        if serializer.is_valid():
            # Создаём User и Profile.
            user = serializer.save()

            # Возвращаем успешный JSON-ответ.
            return Response(
                {
                    'message': 'Пользователь успешно зарегистрирован.',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                    }
                },
                status=status.HTTP_201_CREATED
            )

        # Если данные неправильные, возвращаем ошибки.
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
# Блок 2. API входа пользователя по email.
# Принимает email и password, проверяет их и возвращает токен.
class LoginAPIView(APIView):
    def post(self, request):
        # Блок 2.1. Получаем email и пароль из запроса.
        email = request.data.get('email')
        password = request.data.get('password')

        # Блок 2.2. Проверяем, что оба поля заполнены.
        if not email or not password:
            return Response(
                {'error': 'Необходимо указать email и пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 2.3. Ищем пользователя по email.
        # В стандартной авторизации Django authenticate работает через username,
        # поэтому сначала находим пользователя по email, а потом используем его username.
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Неверный email или пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 2.4. Проверяем пароль через стандартную систему Django.
        user = authenticate(username=user_obj.username, password=password)

        # Блок 2.5. Если пароль неправильный.
        if user is None:
            return Response(
                {'error': 'Неверный email или пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 2.6. Получаем существующий токен или создаём новый.
        token, created = Token.objects.get_or_create(user=user)

        # Блок 2.7. Возвращаем токен и краткие данные пользователя.
        return Response(
            {
                'message': 'Вход выполнен успешно.',
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.profile.role,
                    'role_display': user.profile.get_role_display(),
                }
            },
            status=status.HTTP_200_OK
        )


# Блок 3. API личного кабинета.
# Возвращает данные только авторизованного пользователя.
class ProfileAPIView(APIView):
    # Блок 3.1. Доступ разрешён только пользователю с токеном.
    permission_classes = [IsAuthenticated]

    # Блок 3.2. GET-запрос возвращает данные текущего пользователя.
    def get(self, request):
        serializer = UserProfileSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
