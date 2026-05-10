from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    OrganizerVerification,
    Player,
    Profile,
    Team,
    TeamJoinRequest,
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