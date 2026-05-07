from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('player', 'Игрок команды'),
        ('captain', 'Капитан команды'),
        ('organizer', 'Организатор турниров'),
        ('admin', 'Администратор'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', verbose_name='Роль')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')
    email_confirmed = models.BooleanField(default=False, verbose_name='Email подтверждён')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    def __str__(self):
        return f'{self.user.username} — {self.get_role_display()}'


class Team(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Подтверждена'),
        ('rejected', 'Отклонена'),
    ]

    FORMAT_CHOICES = [
        ('5x5', '5x5'),
        ('6x6', '6x6'),
        ('8x8', '8x8'),
        ('11x11', '11x11'),
    ]

    name = models.CharField(max_length=150, verbose_name='Название команды')
    city = models.CharField(max_length=100, verbose_name='Город')
    game_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, verbose_name='Формат игры')
    description = models.TextField(blank=True, verbose_name='Описание')
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captain_teams', verbose_name='Капитан')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.name


class TeamJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name='Команда')
    position = models.CharField(max_length=100, verbose_name='Позиция')
    age = models.PositiveIntegerField(verbose_name='Возраст')
    number = models.PositiveIntegerField(verbose_name='Игровой номер')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус заявки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подачи')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата рассмотрения')

    def __str__(self):
        return f'{self.user.username} → {self.team.name}'


class Player(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('left', 'Покинул команду'),
        ('removed', 'Удалён из команды'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players', verbose_name='Команда')
    position = models.CharField(max_length=100, verbose_name='Позиция')
    age = models.PositiveIntegerField(verbose_name='Возраст')
    number = models.PositiveIntegerField(verbose_name='Игровой номер')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус игрока')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата вступления')

    def __str__(self):
        return f'{self.user.username} — {self.team.name}'


class OrganizerVerification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Подтверждена'),
        ('rejected', 'Отклонена'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Организатор')
    organization_name = models.CharField(max_length=200, verbose_name='Название организации')
    city = models.CharField(max_length=100, verbose_name='Город')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    experience_description = models.TextField(verbose_name='Описание опыта')
    document = models.FileField(upload_to='organizer_documents/', verbose_name='Подтверждающий документ')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус заявки')
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подачи')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата рассмотрения')

    def __str__(self):
        return f'{self.organization_name} — {self.get_status_display()}'


class Stadium(models.Model):
    name = models.CharField(max_length=150, verbose_name='Название площадки')
    city = models.CharField(max_length=100, verbose_name='Город')
    address = models.CharField(max_length=255, verbose_name='Адрес')
    surface_type = models.CharField(max_length=100, verbose_name='Тип покрытия')

    def __str__(self):
        return f'{self.name}, {self.city}'


class Tournament(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Подтверждён'),
        ('rejected', 'Отклонён'),
        ('registration', 'Идёт набор команд'),
        ('active', 'Активен'),
        ('finished', 'Завершён'),
    ]

    FORMAT_CHOICES = [
        ('5x5', '5x5'),
        ('6x6', '6x6'),
        ('8x8', '8x8'),
        ('11x11', '11x11'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название турнира')
    city = models.CharField(max_length=100, verbose_name='Город')
    game_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, verbose_name='Формат игры')
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(verbose_name='Дата окончания')
    description = models.TextField(blank=True, verbose_name='Описание')
    rules = models.TextField(blank=True, verbose_name='Правила участия')
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_tournaments', verbose_name='Организатор')
    stadium = models.ForeignKey(Stadium, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Площадка')
    confirmation_document = models.FileField(upload_to='tournament_documents/', verbose_name='Подтверждающий документ турнира')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата проверки')

    def __str__(self):
        return self.name


class TournamentApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name='Команда')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, verbose_name='Турнир')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус заявки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подачи')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата рассмотрения')

    def __str__(self):
        return f'{self.team.name} → {self.tournament.name}'


class TournamentSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, verbose_name='Турнир')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подписки')

    def __str__(self):
        return f'{self.user.username} подписан на {self.tournament.name}'


class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланирован'),
        ('played', 'Сыгран'),
        ('cancelled', 'Отменён'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, verbose_name='Турнир')
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches', verbose_name='Команда 1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches', verbose_name='Команда 2')
    stadium = models.ForeignKey(Stadium, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Площадка')
    match_date = models.DateTimeField(verbose_name='Дата и время матча')
    score_team1 = models.PositiveIntegerField(null=True, blank=True, verbose_name='Счёт команды 1')
    score_team2 = models.PositiveIntegerField(null=True, blank=True, verbose_name='Счёт команды 2')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='Статус матча')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f'{self.team1.name} — {self.team2.name}'