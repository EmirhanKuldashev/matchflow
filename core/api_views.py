from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser

from .models import OrganizerVerification, Player, Team, TeamJoinRequest
from .serializers import (
    OrganizerVerificationCreateSerializer,
    OrganizerVerificationSerializer,
    PlayerSerializer,
    RegisterSerializer,
    TeamCreateSerializer,
    TeamJoinRequestCreateSerializer,
    TeamJoinRequestSerializer,
    TeamSerializer,
    UserProfileSerializer,
)

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

# Блок 4. API списка подтверждённых команд.
# Доступен всем пользователям, включая гостей.
class TeamListAPIView(APIView):
    def get(self, request):
        # Показываем только подтверждённые команды.
        teams = Team.objects.filter(status='approved').order_by('-created_at')

        serializer = TeamSerializer(teams, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# Блок 5. API создания команды капитаном.
# Доступен только авторизованному пользователю с ролью captain.
class TeamCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Блок 5.1. Проверяем роль пользователя.
        # Создать команду может только капитан команды.
        if request.user.profile.role != 'captain':
            return Response(
                {'error': 'Создавать команду может только капитан команды.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 5.2. Передаём данные в сериализатор.
        serializer = TeamCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        # Блок 5.3. Если данные корректны, создаём команду.
        if serializer.is_valid():
            team = serializer.save()

            return Response(
                {
                    'message': 'Команда создана и отправлена на проверку администратору.',
                    'team': TeamSerializer(team).data
                },
                status=status.HTTP_201_CREATED
            )

        # Блок 5.4. Если данные некорректны, возвращаем ошибки.
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# Блок 6. API подачи заявки игрока в команду.
# Доступен только авторизованному пользователю с ролью player.
class TeamJoinRequestCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        # Блок 6.1. Проверяем роль пользователя.
        if request.user.profile.role != 'player':
            return Response(
                {'error': 'Подать заявку в команду может только игрок команды.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 6.2. Ищем только подтверждённую команду.
        try:
            team = Team.objects.get(id=team_id, status='approved')
        except Team.DoesNotExist:
            return Response(
                {'error': 'Команда не найдена или ещё не подтверждена.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 6.3. Проверяем, что пользователь ещё не состоит в этой команде.
        if Player.objects.filter(
            user=request.user,
            team=team,
            status='active'
        ).exists():
            return Response(
                {'error': 'Вы уже состоите в этой команде.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 6.4. Проверяем, что нет повторной заявки на проверке.
        if TeamJoinRequest.objects.filter(
            user=request.user,
            team=team,
            status='pending'
        ).exists():
            return Response(
                {'error': 'Вы уже отправили заявку в эту команду.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 6.5. Создаём заявку.
        serializer = TeamJoinRequestCreateSerializer(
            data=request.data,
            context={
                'request': request,
                'team': team,
            }
        )

        if serializer.is_valid():
            join_request = serializer.save()

            return Response(
                {
                    'message': 'Заявка на вступление в команду отправлена капитану.',
                    'request': TeamJoinRequestSerializer(join_request).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# Блок 7. API списка заявок игроков для капитана.
# Капитан видит только заявки в свои команды.
class CaptainJoinRequestListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Блок 7.1. Проверяем роль капитана.
        if request.user.profile.role != 'captain':
            return Response(
                {'error': 'Просматривать заявки может только капитан команды.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 7.2. Получаем заявки только в команды текущего капитана.
        join_requests = TeamJoinRequest.objects.filter(
            team__captain=request.user
        ).order_by('-created_at')

        serializer = TeamJoinRequestSerializer(join_requests, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# Блок 8. API одобрения заявки игрока.
# После одобрения создаётся запись Player.
class TeamJoinRequestApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        # Блок 8.1. Проверяем роль капитана.
        if request.user.profile.role != 'captain':
            return Response(
                {'error': 'Одобрять заявки может только капитан команды.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 8.2. Ищем заявку только в командах текущего капитана.
        try:
            join_request = TeamJoinRequest.objects.get(
                id=request_id,
                team__captain=request.user
            )
        except TeamJoinRequest.DoesNotExist:
            return Response(
                {'error': 'Заявка не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 8.3. Проверяем, что заявка ещё не рассмотрена.
        if join_request.status != 'pending':
            return Response(
                {'error': 'Эта заявка уже была рассмотрена.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 8.4. Одобряем заявку.
        join_request.status = 'approved'
        join_request.reviewed_at = timezone.now()
        join_request.save()

        # Блок 8.5. Создаём игрока команды.
        player = Player.objects.create(
            user=join_request.user,
            team=join_request.team,
            position=join_request.position,
            age=join_request.age,
            number=join_request.number,
            status='active'
        )

        return Response(
            {
                'message': 'Заявка одобрена. Игрок добавлен в команду.',
                'request': TeamJoinRequestSerializer(join_request).data,
                'player': PlayerSerializer(player).data
            },
            status=status.HTTP_200_OK
        )


# Блок 9. API отклонения заявки игрока.
class TeamJoinRequestRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        # Блок 9.1. Проверяем роль капитана.
        if request.user.profile.role != 'captain':
            return Response(
                {'error': 'Отклонять заявки может только капитан команды.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 9.2. Ищем заявку только в командах текущего капитана.
        try:
            join_request = TeamJoinRequest.objects.get(
                id=request_id,
                team__captain=request.user
            )
        except TeamJoinRequest.DoesNotExist:
            return Response(
                {'error': 'Заявка не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 9.3. Проверяем, что заявка ещё не рассмотрена.
        if join_request.status != 'pending':
            return Response(
                {'error': 'Эта заявка уже была рассмотрена.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 9.4. Отклоняем заявку.
        join_request.status = 'rejected'
        join_request.reviewed_at = timezone.now()
        join_request.save()

        return Response(
            {
                'message': 'Заявка отклонена.',
                'request': TeamJoinRequestSerializer(join_request).data
            },
            status=status.HTTP_200_OK
        )
    
# Блок 10. API заявки на подтверждение организатора.
# GET — показывает текущую заявку организатора.
# POST — создаёт новую заявку с подтверждающим документом.
class OrganizerVerificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Блок 10.1. Разрешаем загрузку файлов через форму multipart/form-data.
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        # Блок 10.2. Проверяем роль пользователя.
        if request.user.profile.role != 'organizer':
            return Response(
                {'error': 'Заявка на подтверждение доступна только организатору турниров.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 10.3. Ищем последнюю заявку текущего организатора.
        verification = OrganizerVerification.objects.filter(
            user=request.user
        ).order_by('-submitted_at').first()

        if verification is None:
            return Response(
                {'message': 'Заявка на подтверждение организатора ещё не подана.'},
                status=status.HTTP_200_OK
            )

        serializer = OrganizerVerificationSerializer(verification)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        # Блок 10.4. Проверяем роль пользователя.
        if request.user.profile.role != 'organizer':
            return Response(
                {'error': 'Подать заявку может только пользователь с ролью организатора турниров.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 10.5. Если уже есть заявка на проверке, новую не создаём.
        if OrganizerVerification.objects.filter(
            user=request.user,
            status='pending'
        ).exists():
            return Response(
                {'error': 'У вас уже есть заявка на проверке.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 10.6. Если организатор уже подтверждён, новую заявку не создаём.
        if OrganizerVerification.objects.filter(
            user=request.user,
            status='approved'
        ).exists():
            return Response(
                {'error': 'Ваш статус организатора уже подтверждён.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 10.7. Создаём заявку через сериализатор.
        serializer = OrganizerVerificationCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            verification = serializer.save()

            return Response(
                {
                    'message': 'Заявка на подтверждение организатора отправлена администратору.',
                    'verification': OrganizerVerificationSerializer(verification).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )