from datetime import timedelta
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    Profile,
    Team,
    Tournament,
    Match,
    Stadium,
    OrganizerVerification,
)


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные для MatchFlow'

    def handle(self, *args, **options):
        self.stdout.write('Создание demo-данных MatchFlow...')

        cities = ['Красноярск', 'Москва', 'Новосибирск', 'Казань']
        formats = ['5x5', '6x6', '7x7', '8x8']

        # 1. Пользователи-капитаны
        captains = []
        for i in range(1, 9):
            user, _ = User.objects.get_or_create(
                username=f'captain{i}',
                defaults={
                    'email': f'captain{i}@matchflow.local',
                    'first_name': f'Капитан {i}',
                }
            )
            user.set_password('12345678')
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = 'captain'
            profile.city = random.choice(cities)
            profile.phone = f'+790000000{i}'
            if hasattr(profile, 'email_confirmed'):
                profile.email_confirmed = True
            profile.save()

            captains.append(user)

        # 2. Организатор
        organizer, _ = User.objects.get_or_create(
            username='organizer1',
            defaults={
                'email': 'organizer1@matchflow.local',
                'first_name': 'Организатор',
            }
        )
        organizer.set_password('12345678')
        organizer.save()

        organizer_profile, _ = Profile.objects.get_or_create(user=organizer)
        organizer_profile.role = 'organizer'
        organizer_profile.city = 'Красноярск'
        organizer_profile.phone = '+79990000000'
        if hasattr(organizer_profile, 'email_confirmed'):
            organizer_profile.email_confirmed = True
        organizer_profile.save()

        OrganizerVerification.objects.get_or_create(
            user=organizer,
            defaults={
                'organization_name': 'MatchFlow Demo League',
                'city': 'Красноярск',
                'phone': '+79990000000',
                'experience_description': 'Организация любительских футбольных турниров.',
                'comment': 'Демонстрационная подтверждённая заявка.',
                'status': 'approved',
            }
        )

        # 3. Стадионы
        stadiums = []
        stadium_names = [
            'Манеж Футбол Арена',
            'Стадион Центральный',
            'Парк Арена',
            'Сибирь Спорт',
        ]

        for i, name in enumerate(stadium_names, start=1):
            stadium, _ = Stadium.objects.get_or_create(
                name=name,
                defaults={
                    'city': random.choice(cities),
                    'address': f'ул. Спортивная, {i}',
                    'surface_type': random.choice(['искусственная трава', 'натуральный газон', 'паркет']),
                }
            )
            stadiums.append(stadium)

        # 4. Команды
        team_names = [
            'Красные Барсы',
            'Сибирские Волки',
            'Енисей Юнайтед',
            'ФК Север',
            'Торпедо Парк',
            'Олимпик',
            'Метеор',
            'Стрела',
        ]

        teams = []
        for i, name in enumerate(team_names):
            team, _ = Team.objects.get_or_create(
                name=name,
                defaults={
                    'city': random.choice(cities),
                    'game_format': random.choice(formats),
                    'description': f'Демонстрационная команда {name}.',
                    'captain': captains[i],
                    'status': 'approved',
                }
            )
            team.status = 'approved'
            team.save()
            teams.append(team)

        # 5. Турниры
        tournaments = []
        tournament_names = [
            'Кубок MatchFlow',
            'Летняя лига 5x5',
            'Сибирский мини-футбол',
            'Красноярская футбольная серия',
        ]

        for i, name in enumerate(tournament_names, start=1):
            tournament, _ = Tournament.objects.get_or_create(
                name=name,
                defaults={
                    'city': random.choice(cities),
                    'game_format': random.choice(formats),
                    'start_date': timezone.now().date() + timedelta(days=i * 7),
                    'end_date': timezone.now().date() + timedelta(days=i * 7 + 3),
                    'description': f'Демонстрационный турнир: {name}.',
                    'rules': 'Команды играют по круговой системе. Победа — 3 очка, ничья — 1 очко.',
                    'organizer': organizer,
                    'stadium': random.choice(stadiums),
                    'status': 'registration' if i <= 2 else 'active',
                }
            )
            tournament.status = 'registration' if i <= 2 else 'active'
            tournament.save()
            tournaments.append(tournament)

        # 6. Матчи
        created_matches = 0

        for tournament in tournaments:
            for i in range(12):
                team1, team2 = random.sample(teams, 2)

                match_date = timezone.now() + timedelta(days=i + random.randint(1, 20))

                match, created = Match.objects.get_or_create(
                    tournament=tournament,
                    team1=team1,
                    team2=team2,
                    match_date=match_date,
                    defaults={
                        'stadium': random.choice(stadiums),
                        'status': 'scheduled',
                    }
                )

                # Часть матчей делаем сыгранными
                if i % 3 == 0:
                    match.status = 'played'

                    if hasattr(match, 'score_team1'):
                        match.score_team1 = random.randint(0, 5)
                    if hasattr(match, 'score_team2'):
                        match.score_team2 = random.randint(0, 5)

                    if hasattr(match, 'team1_score'):
                        match.team1_score = random.randint(0, 5)
                    if hasattr(match, 'team2_score'):
                        match.team2_score = random.randint(0, 5)

                    match.save()

                if created:
                    created_matches += 1

        self.stdout.write(self.style.SUCCESS('Demo-данные успешно созданы.'))
        self.stdout.write(self.style.SUCCESS('Пользователи:'))
        self.stdout.write('captain1 ... captain8 / пароль: 12345678')
        self.stdout.write('organizer1 / пароль: 12345678')
        self.stdout.write(self.style.SUCCESS(f'Создано/обновлено команд: {len(teams)}'))
        self.stdout.write(self.style.SUCCESS(f'Создано/обновлено турниров: {len(tournaments)}'))
        self.stdout.write(self.style.SUCCESS(f'Создано новых матчей: {created_matches}'))