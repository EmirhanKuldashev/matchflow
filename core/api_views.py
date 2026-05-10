from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer


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