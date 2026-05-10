from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Profile


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