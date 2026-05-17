from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser
from django.db import models
from .permissions import IsAdminUser

from .models import (
    Match,
    OrganizerVerification,
    Player,
    Team,
    TeamJoinRequest,
    Tournament,
    TournamentApplication,
    TournamentSubscription,
)
from .email_utils import send_email_confirmation
from .serializers import (
    MatchCreateSerializer,
    MatchResultUpdateSerializer,
    MatchSerializer,
    OrganizerVerificationCreateSerializer,
    OrganizerVerificationSerializer,
    PlayerSerializer,
    RegisterSerializer,
    TeamCreateSerializer,
    TeamJoinRequestCreateSerializer,
    TeamJoinRequestSerializer,
    TeamSerializer,
    TournamentApplicationCreateSerializer,
    TournamentApplicationSerializer,
    TournamentCreateSerializer,
    TournamentSerializer,
    TournamentSubscriptionSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)

TOURNAMENT_LIST_CACHE_TIMEOUT = 300

# Блок 0. Универсальная функция пагинации.
# Нужна, чтобы не писать одинаковый код пагинации
# в каждом списочном API: команды, турниры, матчи.
def paginate_queryset(queryset, request, serializer_class, default_page_size=5, max_page_size=50):
    # Блок 0.1. Получаем номер страницы из query-параметра.
    # Например:
    # /api/teams/?page=2
    try:
        page = int(request.query_params.get('page', 1))
    except ValueError:
        page = 1

    # Блок 0.2. Получаем размер страницы.
    # Например:
    # /api/teams/?page_size=10
    try:
        page_size = int(request.query_params.get('page_size', default_page_size))
    except ValueError:
        page_size = default_page_size

    # Блок 0.3. Защита от некорректных значений.
    if page < 1:
        page = 1

    if page_size < 1:
        page_size = default_page_size

    # Блок 0.4. Ограничиваем максимальный размер страницы,
    # чтобы пользователь случайно не запросил слишком много данных.
    if page_size > max_page_size:
        page_size = max_page_size

    # Блок 0.5. Создаём объект пагинатора.
    paginator = Paginator(queryset, page_size)

    # Блок 0.6. Получаем нужную страницу.
    # Если пользователь запросил страницу больше последней,
    # Django вернёт последнюю доступную страницу.
    page_obj = paginator.get_page(page)

    # Блок 0.7. Сериализуем только объекты текущей страницы.
    serializer = serializer_class(
        page_obj.object_list,
        many=True
    )

    # Блок 0.8. Возвращаем единый формат ответа.
    return {
        'count': paginator.count,
        'page': page_obj.number,
        'page_size': page_size,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'results': serializer.data,
    }
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

            # Блок 2.1. Отправляем письмо подтверждения email.
            # В режиме разработки ссылка дополнительно возвращается в JSON.
            confirm_url = send_email_confirmation(user)

            response_data = {
                'message': 'Пользователь успешно зарегистрирован. Проверьте email для подтверждения регистрации.',
                'email_confirmation_required': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            }

            if settings.DEBUG:
                response_data['debug_confirm_url'] = confirm_url

            # Возвращаем успешный JSON-ответ.
            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )

        # Если данные неправильные, возвращаем ошибки.
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# Блок 2.2. API подтверждения email.
# Проверяет token из ссылки и меняет email_confirmed на True.
class ConfirmEmailAPIView(APIView):
    def get(self, request, token):
        signer = TimestampSigner()

        try:
            user_id = signer.unsign(
                token,
                max_age=settings.EMAIL_CONFIRMATION_MAX_AGE
            )
        except SignatureExpired:
            return Response(
                {'error': 'Ссылка подтверждения истекла.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except BadSignature:
            return Response(
                {'error': 'Некорректная ссылка подтверждения.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not hasattr(user, 'profile'):
            return Response(
                {'error': 'У пользователя нет профиля.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.profile.email_confirmed:
            return Response(
                {'message': 'Email уже подтверждён.'},
                status=status.HTTP_200_OK
            )

        user.profile.email_confirmed = True
        user.profile.save()

        return Response(
            {'message': 'Email успешно подтверждён.'},
            status=status.HTTP_200_OK
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

# Блок 3.3. API редактирования профиля пользователя.
# Доступен только авторизованному пользователю.
# Позволяет изменить first_name, last_name, phone и city.
class ProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        # Блок 3.4. Проверяем, что у пользователя есть связанный Profile.
        if not hasattr(request.user, 'profile'):
            return Response(
                {'error': 'У пользователя нет профиля.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 3.5. Передаём частичные данные в сериализатор редактирования.
        serializer = UserProfileUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True
        )

        # Блок 3.6. Если данные корректные, сохраняем и возвращаем обновлённый профиль.
        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    'message': 'Профиль успешно обновлён.',
                    'user': UserProfileSerializer(request.user).data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# Блок 4. API списка подтверждённых команд.
# Доступен всем пользователям, включая гостей.
#
# Поддерживает:
# search — поиск по названию и описанию
# city — фильтр по городу
# game_format — фильтр по формату игры
# page — номер страницы
# page_size — количество записей на странице
class TeamListAPIView(APIView):
    def get(self, request):
        # Блок 4.1. Показываем только подтверждённые команды.
        teams = Team.objects.filter(
            status='approved'
        ).order_by('-created_at')

        # Блок 4.2. Поиск по названию и описанию.
        # Пример:
        # /api/teams/?search=barsy
        search = request.query_params.get('search')

        if search:
            teams = teams.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search)
            )

        # Блок 4.3. Фильтрация по городу.
        # Пример:
        # /api/teams/?city=Krasnoyarsk
        city = request.query_params.get('city')

        if city:
            teams = teams.filter(
                city__icontains=city
            )

        # Блок 4.4. Фильтрация по формату игры.
        # Пример:
        # /api/teams/?game_format=5x5
        game_format = request.query_params.get('game_format')

        if game_format:
            teams = teams.filter(
                game_format=game_format
            )

        # Блок 4.5. Возвращаем результат с пагинацией.
        paginated_data = paginate_queryset(
            queryset=teams,
            request=request,
            serializer_class=TeamSerializer
        )

        return Response(
            paginated_data,
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
# Блок 11. API списка турниров.
# Endpoint:
# GET /api/tournaments/
#
# Доступен всем пользователям.
#
# Поддерживает:
# search — поиск по названию, описанию, правилам
# city — фильтр по городу
# game_format — фильтр по формату игры
# status — фильтр по статусу
# page — номер страницы
# page_size — количество записей на странице
class TournamentListAPIView(APIView):
    # Блок 11.1. Cookie последнего выбранного города.
    # Нужна, чтобы фронтенд мог запомнить последний город фильтрации турниров.
    def set_last_tournament_city_cookie(self, request, response):
        city = request.GET.get('city')

        if city:
            response.set_cookie(
                key='last_tournament_city',
                value=quote(city),
                max_age=60 * 60 * 24 * 30,
                samesite='Lax'
            )

        return response

    def get(self, request):
        # Блок 11.2. Кэширование публичного списка турниров.
        # Нужен, чтобы повторные запросы с одинаковыми фильтрами не обращались к базе данных.
        query_string = request.GET.urlencode()
        cache_key = f'tournament_list:{query_string}'
        cached_response = cache.get(cache_key)

        if cached_response is not None:
            response = Response(
                cached_response,
                status=status.HTTP_200_OK
            )

            return self.set_last_tournament_city_cookie(request, response)

        # Блок 11.3. Получаем только публичные турниры.
        # pending и rejected не показываем обычным пользователям.
        tournaments = Tournament.objects.filter(
            status__in=[
                'approved',
                'registration',
                'active',
                'finished',
            ]
        ).order_by('-created_at')

        # Блок 11.4. Поиск по названию, описанию и правилам.
        # Пример:
        # /api/tournaments/?search=cup
        search = request.query_params.get('search')

        if search:
            tournaments = tournaments.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(rules__icontains=search)
            )

        # Блок 11.5. Фильтрация по городу.
        # Пример:
        # /api/tournaments/?city=Krasnoyarsk
        city = request.query_params.get('city')

        if city:
            tournaments = tournaments.filter(
                city__icontains=city
            )

        # Блок 11.6. Фильтрация по формату игры.
        # Пример:
        # /api/tournaments/?game_format=5x5
        game_format = request.query_params.get('game_format')

        if game_format:
            tournaments = tournaments.filter(
                game_format=game_format
            )

        # Блок 11.7. Фильтрация по статусу.
        # Пример:
        # /api/tournaments/?status=registration
        status_filter = request.query_params.get('status')

        if status_filter:
            tournaments = tournaments.filter(
                status=status_filter
            )

        # Блок 11.8. Возвращаем результат с пагинацией.
        paginated_data = paginate_queryset(
            queryset=tournaments,
            request=request,
            serializer_class=TournamentSerializer
        )

        cache.set(
            cache_key,
            paginated_data,
            TOURNAMENT_LIST_CACHE_TIMEOUT
        )

        response = Response(
            paginated_data,
            status=status.HTTP_200_OK
        )

        return self.set_last_tournament_city_cookie(request, response)
# Блок 12. API подробной информации о турнире.
# Endpoint:
# GET /api/tournaments/<tournament_id>/
#
# Нужен для страницы одного турнира.
class TournamentDetailAPIView(APIView):
    def get(self, request, tournament_id):
        # Блок 12.1. Ищем турнир по id.
        # Но отдаём только публичные турниры.
        try:
            tournament = Tournament.objects.get(
                id=tournament_id,
                status__in=[
                    'approved',
                    'registration',
                    'active',
                    'finished',
                ]
            )
        except Tournament.DoesNotExist:
            return Response(
                {
                    'error': 'Турнир не найден или ещё не подтверждён администратором.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 12.2. Преобразуем турнир в JSON.
        serializer = TournamentSerializer(tournament)

        # Блок 12.3. Возвращаем данные турнира.
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# Блок 13. API создания турнира.
# Endpoint:
# POST /api/tournaments/create/
#
# Доступен только пользователю с ролью organizer,
# причём организатор должен быть подтверждён администратором.
class TournamentCreateAPIView(APIView):
    # Блок 13.1. Создавать турнир может только авторизованный пользователь.
    permission_classes = [IsAuthenticated]

    # Блок 13.2. Разрешаем отправку файлов.
    # Это нужно, потому что при создании турнира
    # организатор прикрепляет подтверждающий документ.
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # Блок 13.3. Проверяем, что у пользователя есть Profile.
        # Суперпользователь, созданный через createsuperuser,
        # может не иметь Profile, поэтому защищаемся от ошибки.
        if not hasattr(request.user, 'profile'):
            return Response(
                {
                    'error': 'У пользователя нет профиля. Создайте пользователя через регистрацию.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 13.4. Проверяем роль пользователя.
        # Турниры может создавать только организатор.
        if request.user.profile.role != 'organizer':
            return Response(
                {
                    'error': 'Создавать турниры может только организатор турниров.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 13.5. Проверяем подтверждение организатора.
        # Просто роль organizer недостаточна.
        # Нужно, чтобы администратор подтвердил OrganizerVerification.
        is_verified_organizer = OrganizerVerification.objects.filter(
            user=request.user,
            status='approved'
        ).exists()

        if not is_verified_organizer:
            return Response(
                {
                    'error': 'Создавать турниры можно только после подтверждения статуса организатора администратором.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 13.6. Передаём данные в сериализатор создания турнира.
        serializer = TournamentCreateSerializer(
            data=request.data,
            context={
                'request': request
            }
        )

        # Блок 13.7. Если данные корректные, создаём турнир.
        if serializer.is_valid():
            tournament = serializer.save()

            return Response(
                {
                    'message': 'Турнир создан и отправлен на проверку администратору.',
                    'tournament': TournamentSerializer(tournament).data
                },
                status=status.HTTP_201_CREATED
            )

        # Блок 13.8. Если данные некорректные, возвращаем ошибки.
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
# Блок 14. API подачи заявки команды на турнир.
# Endpoint:
# POST /api/tournaments/<tournament_id>/apply/
#
# Этот endpoint использует капитан команды.
# Капитан выбирает свою подтверждённую команду
# и подаёт её на участие в турнире.
class TournamentApplicationCreateAPIView(APIView):
    # Блок 14.1. Подать заявку может только авторизованный пользователь.
    permission_classes = [IsAuthenticated]

    def post(self, request, tournament_id):
        # Блок 14.2. Проверяем, что у пользователя есть Profile.
        if not hasattr(request.user, 'profile'):
            return Response(
                {
                    'error': 'У пользователя нет профиля. Создайте пользователя через регистрацию.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 14.3. Проверяем роль.
        # Подать команду на турнир может только капитан.
        if request.user.profile.role != 'captain':
            return Response(
                {
                    'error': 'Подать заявку на турнир может только капитан команды.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 14.4. Ищем турнир.
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response(
                {
                    'error': 'Турнир не найден.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 14.5. Передаём данные в сериализатор.
        serializer = TournamentApplicationCreateSerializer(
            data=request.data,
            context={
                'request': request,
                'tournament': tournament,
            }
        )

        # Блок 14.6. Если данные корректные — создаём заявку.
        if serializer.is_valid():
            application = serializer.save()

            return Response(
                {
                    'message': 'Заявка команды на участие в турнире отправлена организатору.',
                    'application': TournamentApplicationSerializer(application).data
                },
                status=status.HTTP_201_CREATED
            )

        # Блок 14.7. Если данные некорректные — возвращаем ошибки.
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# Блок 15. API списка заявок на турниры организатора.
# Endpoint:
# GET /api/organizer/tournament-applications/
#
# Организатор видит заявки только на свои турниры.
class OrganizerTournamentApplicationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Блок 15.1. Проверяем Profile.
        if not hasattr(request.user, 'profile'):
            return Response(
                {
                    'error': 'У пользователя нет профиля.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 15.2. Проверяем роль.
        if request.user.profile.role != 'organizer':
            return Response(
                {
                    'error': 'Просматривать заявки может только организатор турнира.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 15.3. Получаем заявки только на турниры текущего организатора.
        applications = TournamentApplication.objects.filter(
            tournament__organizer=request.user
        ).order_by('-created_at')

        # Блок 15.4. Фильтр по статусу.
        # Пример:
        # /api/organizer/tournament-applications/?status=pending
        status_filter = request.query_params.get('status')

        if status_filter:
            applications = applications.filter(status=status_filter)

        # Блок 15.5. Фильтр по турниру.
        # Пример:
        # /api/organizer/tournament-applications/?tournament=1
        tournament_id = request.query_params.get('tournament')

        if tournament_id:
            applications = applications.filter(tournament_id=tournament_id)

        # Блок 15.6. Превращаем заявки в JSON.
        serializer = TournamentApplicationSerializer(
            applications,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# Блок 16. API одобрения заявки команды на турнир.
# Endpoint:
# POST /api/tournament-applications/<application_id>/approve/
#
# Доступен только организатору турнира.
class TournamentApplicationApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        # Блок 16.1. Проверяем Profile.
        if not hasattr(request.user, 'profile'):
            return Response(
                {
                    'error': 'У пользователя нет профиля.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 16.2. Проверяем роль организатора.
        if request.user.profile.role != 'organizer':
            return Response(
                {
                    'error': 'Одобрять заявки может только организатор турнира.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 16.3. Ищем заявку только среди турниров текущего организатора.
        try:
            application = TournamentApplication.objects.get(
                id=application_id,
                tournament__organizer=request.user
            )
        except TournamentApplication.DoesNotExist:
            return Response(
                {
                    'error': 'Заявка не найдена.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 16.4. Проверяем, что заявка ещё не была рассмотрена.
        if application.status != 'pending':
            return Response(
                {
                    'error': 'Эта заявка уже была рассмотрена.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 16.5. Одобряем заявку.
        application.status = 'approved'
        application.reviewed_at = timezone.now()
        application.save()

        return Response(
            {
                'message': 'Заявка команды на турнир одобрена.',
                'application': TournamentApplicationSerializer(application).data
            },
            status=status.HTTP_200_OK
        )


# Блок 17. API отклонения заявки команды на турнир.
# Endpoint:
# POST /api/tournament-applications/<application_id>/reject/
#
# Доступен только организатору турнира.
class TournamentApplicationRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        # Блок 17.1. Проверяем Profile.
        if not hasattr(request.user, 'profile'):
            return Response(
                {
                    'error': 'У пользователя нет профиля.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 17.2. Проверяем роль организатора.
        if request.user.profile.role != 'organizer':
            return Response(
                {
                    'error': 'Отклонять заявки может только организатор турнира.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 17.3. Ищем заявку только среди турниров текущего организатора.
        try:
            application = TournamentApplication.objects.get(
                id=application_id,
                tournament__organizer=request.user
            )
        except TournamentApplication.DoesNotExist:
            return Response(
                {
                    'error': 'Заявка не найдена.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 17.4. Проверяем, что заявка ещё pending.
        if application.status != 'pending':
            return Response(
                {
                    'error': 'Эта заявка уже была рассмотрена.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 17.5. Отклоняем заявку.
        application.status = 'rejected'
        application.reviewed_at = timezone.now()
        application.save()

        return Response(
            {
                'message': 'Заявка команды на турнир отклонена.',
                'application': TournamentApplicationSerializer(application).data
            },
            status=status.HTTP_200_OK
        )
# Блок 18. API списка матчей.
# Endpoint:
# GET /api/matches/
#
# Доступен всем пользователям.
#
# Поддерживает:
# search — поиск по турниру, командам и стадиону
# tournament — фильтр по турниру
# team — фильтр по команде
# status — фильтр по статусу матча
# page — номер страницы
# page_size — количество записей на странице
class MatchListAPIView(APIView):
    def get(self, request):
        # Блок 18.1. Получаем все матчи.
        matches = Match.objects.all().order_by('match_date')

        # Блок 18.2. Поиск по названию турнира, команд и стадиона.
        # Пример:
        # /api/matches/?search=barsy
        search = request.query_params.get('search')

        if search:
            matches = matches.filter(
                models.Q(tournament__name__icontains=search) |
                models.Q(team1__name__icontains=search) |
                models.Q(team2__name__icontains=search) |
                models.Q(stadium__name__icontains=search)
            )

        # Блок 18.3. Фильтр по турниру.
        # Пример:
        # /api/matches/?tournament=1
        tournament_id = request.query_params.get('tournament')

        if tournament_id:
            matches = matches.filter(
                tournament_id=tournament_id
            )

        # Блок 18.4. Фильтр по статусу.
        # Пример:
        # /api/matches/?status=scheduled
        status_filter = request.query_params.get('status')

        if status_filter:
            matches = matches.filter(
                status=status_filter
            )

        # Блок 18.5. Фильтр по команде.
        # Покажет матчи, где команда является team1 или team2.
        # Пример:
        # /api/matches/?team=1
        team_id = request.query_params.get('team')

        if team_id:
            matches = matches.filter(
                models.Q(team1_id=team_id) |
                models.Q(team2_id=team_id)
            )

        # Блок 18.6. Возвращаем результат с пагинацией.
        paginated_data = paginate_queryset(
            queryset=matches,
            request=request,
            serializer_class=MatchSerializer
        )

        return Response(
            paginated_data,
            status=status.HTTP_200_OK
        )
# Блок 19. API подробной информации о матче.
# Endpoint:
# GET /api/matches/<match_id>/
class MatchDetailAPIView(APIView):
    def get(self, request, match_id):
        # Блок 19.1. Ищем матч.
        try:
            match = Match.objects.get(id=match_id)
        except Match.DoesNotExist:
            return Response(
                {
                    'error': 'Матч не найден.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 19.2. Превращаем матч в JSON.
        serializer = MatchSerializer(match)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# Блок 20. API создания матча.
# Endpoint:
# POST /api/matches/create/
#
# Матч создаёт организатор турнира.
class MatchCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Блок 20.1. Проверяем Profile.
        if not hasattr(request.user, 'profile'):
            return Response(
                {
                    'error': 'У пользователя нет профиля.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 20.2. Проверяем роль.
        if request.user.profile.role != 'organizer':
            return Response(
                {
                    'error': 'Создавать матчи может только организатор турнира.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 20.3. Передаём данные в сериализатор.
        serializer = MatchCreateSerializer(
            data=request.data,
            context={
                'request': request
            }
        )

        # Блок 20.4. Если данные корректны — создаём матч.
        if serializer.is_valid():
            match = serializer.save()

            return Response(
                {
                    'message': 'Матч успешно создан.',
                    'match': MatchSerializer(match).data
                },
                status=status.HTTP_201_CREATED
            )

        # Блок 20.5. Если данные некорректны — возвращаем ошибки.
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# Блок 21. API внесения результата матча.
# Endpoint:
# PATCH /api/matches/<match_id>/result/
#
# Результат может внести только организатор турнира.
class MatchResultUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, match_id):
        # Блок 21.1. Проверяем Profile.
        if not hasattr(request.user, 'profile'):
            return Response(
                {
                    'error': 'У пользователя нет профиля.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 21.2. Проверяем роль.
        if request.user.profile.role != 'organizer':
            return Response(
                {
                    'error': 'Вносить результат может только организатор турнира.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 21.3. Ищем матч только среди турниров текущего организатора.
        try:
            match = Match.objects.get(
                id=match_id,
                tournament__organizer=request.user
            )
        except Match.DoesNotExist:
            return Response(
                {
                    'error': 'Матч не найден.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 21.4. Проверяем, что матч ещё не сыгран.
        if match.status == 'played':
            return Response(
                {
                    'error': 'Результат этого матча уже внесён.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 21.5. Передаём данные результата в сериализатор.
        serializer = MatchResultUpdateSerializer(
            match,
            data=request.data,
            partial=True
        )

        # Блок 21.6. Если данные корректны — сохраняем результат.
        if serializer.is_valid():
            match = serializer.save()

            return Response(
                {
                    'message': 'Результат матча успешно сохранён.',
                    'match': MatchSerializer(match).data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
# Блок 22. API подписки пользователя на турнир.
# Endpoint:
# POST /api/tournaments/<tournament_id>/subscribe/
#
# Этот endpoint нужен обычному пользователю, игроку, капитану или организатору,
# чтобы добавить турнир в список "Мои турниры".
class TournamentSubscribeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tournament_id):
        # Блок 22.1. Проверяем, что у пользователя есть профиль.
        if not hasattr(request.user, 'profile'):
            return Response(
                {
                    'error': 'У пользователя нет профиля. Создайте пользователя через регистрацию.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Блок 22.2. Ищем публичный турнир.
        # Нельзя подписываться на турнир, который ещё на проверке или отклонён.
        try:
            tournament = Tournament.objects.get(
                id=tournament_id,
                status__in=[
                    'approved',
                    'registration',
                    'active',
                    'finished',
                ]
            )
        except Tournament.DoesNotExist:
            return Response(
                {
                    'error': 'Турнир не найден или ещё не опубликован.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Блок 22.3. Создаём подписку, если её ещё нет.
        # get_or_create защищает от повторных одинаковых подписок.
        subscription, created = TournamentSubscription.objects.get_or_create(
            user=request.user,
            tournament=tournament
        )

        # Блок 22.4. Если подписка уже была, сообщаем об этом.
        if not created:
            return Response(
                {
                    'message': 'Вы уже подписаны на этот турнир.',
                    'subscription': TournamentSubscriptionSerializer(subscription).data
                },
                status=status.HTTP_200_OK
            )

        # Блок 22.5. Возвращаем созданную подписку.
        return Response(
            {
                'message': 'Вы успешно подписались на турнир.',
                'subscription': TournamentSubscriptionSerializer(subscription).data
            },
            status=status.HTTP_201_CREATED
        )


# Блок 23. API отписки пользователя от турнира.
# Endpoint:
# POST /api/tournaments/<tournament_id>/unsubscribe/
#
# Этот endpoint удаляет запись TournamentSubscription.
class TournamentUnsubscribeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tournament_id):
        # Блок 23.1. Ищем подписку текущего пользователя на этот турнир.
        subscription = TournamentSubscription.objects.filter(
            user=request.user,
            tournament_id=tournament_id
        ).first()

        # Блок 23.2. Если подписки нет, возвращаем понятный ответ.
        if subscription is None:
            return Response(
                {
                    'error': 'Вы не подписаны на этот турнир.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Блок 23.3. Удаляем подписку.
        subscription.delete()

        return Response(
            {
                'message': 'Вы успешно отписались от турнира.'
            },
            status=status.HTTP_200_OK
        )


# Блок 24. API списка турниров, на которые подписан пользователь.
# Endpoint:
# GET /api/my-tournaments/
#
# Этот endpoint нужен для личного кабинета:
# пользователь видит список турниров, за которыми следит.
class MyTournamentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Блок 24.1. Получаем подписки только текущего пользователя.
        subscriptions = TournamentSubscription.objects.filter(
            user=request.user
        ).select_related(
            'tournament',
            'user'
        ).order_by('-created_at')

        # Блок 24.2. Превращаем подписки в JSON.
        serializer = TournamentSubscriptionSerializer(
            subscriptions,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

class AdminTeamApproveAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, team_id):
        team = Team.objects.get(id=team_id)
        team.status = 'approved'
        team.save()
        return Response({'message': 'Команда подтверждена'})

class AdminTeamRejectAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, team_id):
        team = Team.objects.get(id=team_id)
        team.status = 'rejected'
        team.save()
        return Response({'message': 'Команда отклонена'})

class TeamUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, team_id):
        team = Team.objects.get(id=team_id, captain=request.user)
        serializer = TeamCreateSerializer(team, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'team': TeamSerializer(team).data})
        return Response(serializer.errors, status=400)

class TournamentUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, tournament_id):
        tournament = Tournament.objects.get(id=tournament_id, organizer=request.user)
        serializer = TournamentCreateSerializer(tournament, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'tournament': TournamentSerializer(tournament).data})
        return Response(serializer.errors, status=400)

class MatchUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, match_id):
        match = Match.objects.get(id=match_id, tournament__organizer=request.user)
        serializer = MatchCreateSerializer(match, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'match': MatchSerializer(match).data})
        return Response(serializer.errors, status=400)

class MatchCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id):
        match = Match.objects.get(id=match_id, tournament__organizer=request.user)
        if match.status == 'played':
            return Response({'error': 'Нельзя отменить сыгранный матч'}, 400)
        match.status = 'cancelled'
        match.save()
        return Response({'message': 'Матч отменён'})

class MatchRescheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, match_id):
        match = Match.objects.get(id=match_id, tournament__organizer=request.user)
        match.match_date = request.data.get('match_date')
        match.save()
        return Response({'message': 'Матч перенесён'})