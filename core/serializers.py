from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Match,
    OrganizerVerification,
    Player,
    Profile,
    Stadium,
    Team,
    TeamJoinRequest,
    Tournament,
    TournamentApplication,
    TournamentSubscription,
)
# Блок 1. Сериализатор регистрации
# Сериализатор принимает данные из API-запроса,
# проверяет их и создаёт User + Profile.
class RegisterSerializer(serializers.ModelSerializer):
    # Блок 2. Список ролей, доступных при регистрации.
    # Администратора здесь нет, потому что он создаётся через Django admin.
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('player', 'Игрок команды'),
        ('captain', 'Капитан команды'),
        ('organizer', 'Организатор турниров'),
    ]

    # Блок 3. Дополнительные поля, которых нет в стандартной модели User.
    # Они нужны для создания Profile.
    phone = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES)

    # Блок 4. Поля пароля.
    # write_only=True означает, что пароль можно отправить на сервер,
    # но он не будет возвращаться в ответе API.
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    # Блок 5. Настройки сериализатора.
    # Основная модель — стандартный User.
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'city',
            'role',
            'password',
            'password2',
        ]

    # Блок 6. Проверка данных.
    # Здесь проверяем, что два пароля совпадают.
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                'password': 'Пароли не совпадают.'
            })

        return data

    # Блок 7. Создание пользователя.
    # Здесь создаются две записи: User и Profile.
    def create(self, validated_data):
        # Забираем данные профиля отдельно,
        # потому что в модели User таких полей нет.
        phone = validated_data.pop('phone', '')
        city = validated_data.pop('city', '')
        role = validated_data.pop('role')

        # Второй пароль нужен только для проверки,
        # в базу его сохранять не надо.
        validated_data.pop('password2')

        password = validated_data.pop('password')

        # Создаём стандартного пользователя Django.
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=password
        )

        # Создаём связанный профиль пользователя.
        Profile.objects.create(
            user=user,
            role=role,
            phone=phone,
            city=city,
            email_confirmed=False
        )

        return user
    
# Блок 8. Сериализатор профиля пользователя.
# Нужен, чтобы API мог вернуть данные Profile текущего пользователя.
class ProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'role',
            'role_display',
            'phone',
            'city',
            'email_confirmed',
            'created_at',
        ]


# Блок 9. Сериализатор текущего пользователя.
# Нужен для API личного кабинета.
# Возвращает данные User и вложенные данные Profile.
class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'profile',
        ]

# Блок 9.1. Сериализатор редактирования профиля пользователя.
# Нужен, чтобы пользователь мог изменить имя, фамилию, телефон и город.
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone',
            'city',
        ]

    # Блок 9.2. Обновление данных пользователя и связанного профиля.
    # Поля User сохраняются в User, а телефон и город — в Profile.
    def update(self, instance, validated_data):
        profile = instance.profile

        if 'first_name' in validated_data:
            instance.first_name = validated_data['first_name']

        if 'last_name' in validated_data:
            instance.last_name = validated_data['last_name']

        if 'phone' in validated_data:
            profile.phone = validated_data['phone']

        if 'city' in validated_data:
            profile.city = validated_data['city']

        instance.save()
        profile.save()

        return instance

# Блок 10. Сериализатор списка команд.
# Нужен, чтобы API возвращал данные подтверждённых команд.
class TeamSerializer(serializers.ModelSerializer):
    captain_username = serializers.CharField(source='captain.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    game_format_display = serializers.CharField(source='get_game_format_display', read_only=True)

    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'city',
            'game_format',
            'game_format_display',
            'description',
            'captain_username',
            'status',
            'status_display',
            'created_at',
        ]


# Блок 11. Сериализатор создания команды.
# Нужен, чтобы капитан мог отправить команду на проверку.
class TeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = [
            'name',
            'city',
            'game_format',
            'description',
        ]

    # Блок 11.1. Создание команды.
    # Капитан берётся автоматически из request.user во view.
    # Статус команды сразу ставится "На проверке".
    def create(self, validated_data):
        request = self.context.get('request')

        team = Team.objects.create(
            captain=request.user,
            status='pending',
            **validated_data
        )

        return team

# Блок 12. Сериализатор заявки игрока на вступление в команду.
# Нужен, чтобы игрок мог отправить заявку капитану команды.
class TeamJoinRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamJoinRequest
        fields = [
            'position',
            'age',
            'number',
            'comment',
        ]

    # Блок 12.1. Создание заявки.
    # Пользователь и команда не выбираются вручную в форме:
    # user берём из request.user, team берём из URL.
    def create(self, validated_data):
        request = self.context.get('request')
        team = self.context.get('team')

        join_request = TeamJoinRequest.objects.create(
            user=request.user,
            team=team,
            status='pending',
            **validated_data
        )

        return join_request


# Блок 13. Сериализатор просмотра заявок на вступление в команду.
# Нужен капитану, чтобы видеть, кто хочет вступить в его команду.
class TeamJoinRequestSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TeamJoinRequest
        fields = [
            'id',
            'user',
            'user_username',
            'user_email',
            'team',
            'team_name',
            'position',
            'age',
            'number',
            'comment',
            'status',
            'status_display',
            'created_at',
            'reviewed_at',
        ]


# Блок 14. Сериализатор игрока команды.
# Нужен, чтобы вернуть данные созданного игрока после одобрения заявки.
class PlayerSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Player
        fields = [
            'id',
            'user',
            'user_username',
            'team',
            'team_name',
            'position',
            'age',
            'number',
            'status',
            'status_display',
            'joined_at',
        ]

# Блок 15. Сериализатор просмотра заявки организатора.
# Нужен, чтобы вернуть пользователю данные его заявки на подтверждение.
class OrganizerVerificationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrganizerVerification
        fields = [
            'id',
            'username',
            'user_email',
            'organization_name',
            'city',
            'phone',
            'experience_description',
            'document',
            'comment',
            'status',
            'status_display',
            'submitted_at',
            'reviewed_at',
        ]


# Блок 16. Сериализатор создания заявки организатора.
# Нужен, чтобы пользователь с ролью organizer мог отправить заявку с документом.
class OrganizerVerificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizerVerification
        fields = [
            'organization_name',
            'city',
            'phone',
            'experience_description',
            'document',
            'comment',
        ]

    # Блок 16.1. Создание заявки.
    # Пользователь берётся автоматически из request.user.
    # Статус сразу ставится "На проверке".
    def create(self, validated_data):
        request = self.context.get('request')

        verification = OrganizerVerification.objects.create(
            user=request.user,
            status='pending',
            **validated_data
        )

        return verification
# Блок 17. Сериализатор площадки.
# Этот сериализатор нужен для того, чтобы API турниров мог возвращать
# не только id площадки, но и понятную информацию о ней:
# название, город, адрес и тип покрытия.
class StadiumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stadium
        fields = [
            'id',
            'name',
            'city',
            'address',
            'surface_type',
        ]


# Блок 18. Сериализатор просмотра турнира.
# Используется для:
# GET /api/tournaments/
# GET /api/tournaments/<id>/
#
# Он превращает объект Tournament из базы данных в JSON,
# который потом сможет получить React.
class TournamentSerializer(serializers.ModelSerializer):
    # Блок 18.1. Имя пользователя-организатора.
    # В модели Tournament хранится organizer как ForeignKey на User,
    # а frontend удобнее сразу получить username организатора.
    organizer_username = serializers.CharField(
        source='organizer.username',
        read_only=True
    )

    # Блок 18.2. Данные площадки.
    # Вместо того чтобы отдавать только stadium = 1,
    # мы дополнительно отдаём объект stadium_info с подробностями.
    stadium_info = StadiumSerializer(
        source='stadium',
        read_only=True
    )

    # Блок 18.3. Человекочитаемый статус.
    # Например, status = "pending",
    # а status_display = "На проверке".
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    # Блок 18.4. Человекочитаемый формат игры.
    # Например, game_format = "5x5".
    game_format_display = serializers.CharField(
        source='get_game_format_display',
        read_only=True
    )

    class Meta:
        model = Tournament
        fields = [
            'id',
            'name',
            'city',
            'game_format',
            'game_format_display',
            'start_date',
            'end_date',
            'description',
            'rules',
            'organizer',
            'organizer_username',
            'stadium',
            'stadium_info',
            'confirmation_document',
            'status',
            'status_display',
            'created_at',
            'reviewed_at',
        ]


# Блок 19. Сериализатор создания турнира.
# Используется для:
# POST /api/tournaments/create/
#
# Важно:
# organizer не приходит с frontend — он берётся из request.user.
# status не приходит с frontend — он автоматически ставится pending.
class TournamentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = [
            'name',
            'city',
            'game_format',
            'start_date',
            'end_date',
            'description',
            'rules',
            'stadium',
            'confirmation_document',
        ]

    # Блок 19.1. Общая проверка данных турнира.
    # Здесь проверяем, что дата окончания турнира
    # не раньше даты начала.
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': 'Дата окончания не может быть раньше даты начала.'
            })

        return data

    # Блок 19.2. Создание турнира.
    # Здесь мы создаём объект Tournament в базе данных.
    def create(self, validated_data):
        # Получаем request, который передали из view.
        request = self.context.get('request')

        # Создаём турнир:
        # organizer = текущий пользователь;
        # status = pending, то есть "На проверке";
        # остальные поля берём из validated_data.
        tournament = Tournament.objects.create(
            organizer=request.user,
            status='pending',
            **validated_data
        )

        return tournament
# Блок 20. Сериализатор просмотра заявки команды на турнир.
# Используется для:
# GET /api/organizer/tournament-applications/
#
# Этот сериализатор превращает объект TournamentApplication
# в JSON для frontend или проверки через браузер/Postman.
class TournamentApplicationSerializer(serializers.ModelSerializer):
    # Блок 20.1. Название команды.
    # В базе хранится team_id, но frontend удобнее получить ещё и team_name.
    team_name = serializers.CharField(
        source='team.name',
        read_only=True
    )

    # Блок 20.2. Название турнира.
    tournament_name = serializers.CharField(
        source='tournament.name',
        read_only=True
    )

    # Блок 20.3. Username капитана команды.
    captain_username = serializers.CharField(
        source='team.captain.username',
        read_only=True
    )

    # Блок 20.4. Красивое отображение статуса.
    # Например:
    # status = "pending"
    # status_display = "На проверке"
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = TournamentApplication
        fields = [
            'id',
            'team',
            'team_name',
            'captain_username',
            'tournament',
            'tournament_name',
            'comment',
            'status',
            'status_display',
            'created_at',
            'reviewed_at',
        ]


# Блок 21. Сериализатор создания заявки команды на турнир.
# Используется для:
# POST /api/tournaments/<tournament_id>/apply/
#
# Капитан передаёт team_id и comment.
# Сам tournament берётся из URL.
class TournamentApplicationCreateSerializer(serializers.ModelSerializer):
    # Блок 21.1. ID команды, которую капитан хочет подать на турнир.
    team_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TournamentApplication
        fields = [
            'team_id',
            'comment',
        ]

    # Блок 21.2. Проверка данных перед созданием заявки.
    def validate(self, data):
        # Получаем request и tournament из context.
        request = self.context.get('request')
        tournament = self.context.get('tournament')

        team_id = data.get('team_id')

        # Блок 21.3. Проверяем, существует ли команда.
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            raise serializers.ValidationError({
                'team_id': 'Команда не найдена.'
            })

        # Блок 21.4. Проверяем, что текущий пользователь — капитан этой команды.
        # Нельзя подать чужую команду на турнир.
        if team.captain != request.user:
            raise serializers.ValidationError({
                'team_id': 'Вы можете подать заявку только от своей команды.'
            })

        # Блок 21.5. Проверяем, что команда подтверждена администратором.
        if team.status != 'approved':
            raise serializers.ValidationError({
                'team_id': 'Команда должна быть подтверждена администратором.'
            })

        # Блок 21.6. Проверяем статус турнира.
        # Подавать заявку можно только на подтверждённый турнир
        # или на турнир, где уже открыт набор команд.
        if tournament.status not in ['approved', 'registration']:
            raise serializers.ValidationError({
                'tournament': 'На этот турнир сейчас нельзя подать заявку.'
            })

        # Блок 21.7. Проверяем, что такая заявка ещё не существует.
        if TournamentApplication.objects.filter(
            team=team,
            tournament=tournament
        ).exists():
            raise serializers.ValidationError({
                'team_id': 'Эта команда уже подавала заявку на данный турнир.'
            })

        # Блок 21.8. Сохраняем найденную команду,
        # чтобы использовать её в create().
        data['team'] = team

        return data

    # Блок 21.9. Создание заявки.
    def create(self, validated_data):
        tournament = self.context.get('tournament')

        # team_id не является полем модели,
        # поэтому удаляем его перед созданием объекта.
        validated_data.pop('team_id')

        application = TournamentApplication.objects.create(
            tournament=tournament,
            status='pending',
            **validated_data
        )

        return application
# Блок 22. Сериализатор просмотра матча.
# Используется для:
# GET /api/matches/
# GET /api/matches/<match_id>/
#
# Он нужен, чтобы frontend получил не только id связанных объектов,
# но и понятные названия турнира, команд и стадиона.
class MatchSerializer(serializers.ModelSerializer):
    # Блок 22.1. Название турнира.
    tournament_name = serializers.CharField(
        source='tournament.name',
        read_only=True
    )

    # Блок 22.2. Название первой команды.
    team1_name = serializers.CharField(
        source='team1.name',
        read_only=True
    )

    # Блок 22.3. Название второй команды.
    team2_name = serializers.CharField(
        source='team2.name',
        read_only=True
    )

    # Блок 22.4. Название стадиона.
    stadium_name = serializers.CharField(
        source='stadium.name',
        read_only=True
    )

    # Блок 22.5. Красивое отображение статуса матча.
    # Например:
    # status = "scheduled"
    # status_display = "Запланирован"
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Match
        fields = [
            'id',
            'tournament',
            'tournament_name',
            'team1',
            'team1_name',
            'team2',
            'team2_name',
            'stadium',
            'stadium_name',
            'match_date',
            'score_team1',
            'score_team2',
            'status',
            'status_display',
            'created_at',
        ]


# Блок 23. Сериализатор создания матча.
# Используется для:
# POST /api/matches/create/
#
# Организатор передаёт:
# tournament, team1, team2, stadium, match_date.
# Статус автоматически ставится scheduled.
class MatchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = [
            'tournament',
            'team1',
            'team2',
            'stadium',
            'match_date',
        ]

    # Блок 23.1. Проверка данных матча.
    def validate(self, data):
        request = self.context.get('request')

        tournament = data.get('tournament')
        team1 = data.get('team1')
        team2 = data.get('team2')

        # Блок 23.2. Проверяем, что организатор создаёт матч только в своём турнире.
        if tournament.organizer != request.user:
            raise serializers.ValidationError({
                'tournament': 'Вы можете создавать матчи только в своих турнирах.'
            })

        # Блок 23.3. Проверяем статус турнира.
        # Матчи можно создавать только для подтверждённого или активного турнира.
        if tournament.status not in ['approved', 'registration', 'active']:
            raise serializers.ValidationError({
                'tournament': 'Для этого турнира сейчас нельзя создавать матчи.'
            })

        # Блок 23.4. Проверяем, что команды разные.
        if team1 == team2:
            raise serializers.ValidationError({
                'team2': 'Команды в матче должны быть разными.'
            })

        # Блок 23.5. Проверяем, что первая команда одобрена на этот турнир.
        team1_approved = TournamentApplication.objects.filter(
            tournament=tournament,
            team=team1,
            status='approved'
        ).exists()

        if not team1_approved:
            raise serializers.ValidationError({
                'team1': 'Команда 1 не одобрена для участия в этом турнире.'
            })

        # Блок 23.6. Проверяем, что вторая команда одобрена на этот турнир.
        team2_approved = TournamentApplication.objects.filter(
            tournament=tournament,
            team=team2,
            status='approved'
        ).exists()

        if not team2_approved:
            raise serializers.ValidationError({
                'team2': 'Команда 2 не одобрена для участия в этом турнире.'
            })

        return data

    # Блок 23.7. Создание матча.
    def create(self, validated_data):
        match = Match.objects.create(
            status='scheduled',
            **validated_data
        )

        return match


# Блок 24. Сериализатор внесения результата матча.
# Используется для:
# PATCH /api/matches/<match_id>/result/
#
# Организатор передаёт счёт двух команд.
class MatchResultUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = [
            'score_team1',
            'score_team2',
        ]

    # Блок 24.1. Проверяем, что оба счёта заполнены.
    def validate(self, data):
        score_team1 = data.get('score_team1')
        score_team2 = data.get('score_team2')

        if score_team1 is None or score_team2 is None:
            raise serializers.ValidationError({
                'score': 'Необходимо указать счёт обеих команд.'
            })

        return data

    # Блок 24.2. Обновляем результат матча.
    # После внесения счёта матч становится сыгранным.
    def update(self, instance, validated_data):
        instance.score_team1 = validated_data.get('score_team1')
        instance.score_team2 = validated_data.get('score_team2')
        instance.status = 'played'
        instance.save()

        return instance
# Блок 25. Сериализатор подписки пользователя на турнир.
# Используется для:
# GET /api/my-tournaments/
#
# Эта модель связывает пользователя и турнир.
# То есть одна запись TournamentSubscription означает:
# конкретный пользователь подписан на конкретный турнир.
class TournamentSubscriptionSerializer(serializers.ModelSerializer):
    # Блок 25.1. Подробная информация о турнире.
    # В базе хранится только tournament_id,
    # но frontend удобнее получить сразу данные турнира.
    tournament_info = TournamentSerializer(
        source='tournament',
        read_only=True
    )

    # Блок 25.2. Username пользователя.
    # Это поле удобно для проверки в API и админке.
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = TournamentSubscription
        fields = [
            'id',
            'user',
            'username',
            'tournament',
            'tournament_info',
            'created_at',
        ]
