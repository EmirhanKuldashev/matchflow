from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Profile


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('player', 'Игрок команды'),
        ('captain', 'Капитан команды'),
        ('organizer', 'Организатор турниров'),
    ]

    email = forms.EmailField(
        required=True,
        label='Email'
    )

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='Имя'
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        label='Фамилия'
    )

    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Телефон'
    )

    city = forms.CharField(
        max_length=100,
        required=False,
        label='Город'
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label='Роль'
    )

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
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

            Profile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone=self.cleaned_data['phone'],
                city=self.cleaned_data['city'],
                email_confirmed=False
            )

        return user