from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import (
    Profile, Team, TeamJoinRequest, Player, OrganizerVerification,
    Tournament, TournamentApplication, Match, Stadium, TournamentSubscription
)

class MatchFlowFullAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # Общий стадион для всех тестов
        cls.stadium = Stadium.objects.create(
            name='Main Stadium', city='Test City', address='123 Street', surface_type='grass'
        )

    # --------------------
    # Регистрация и логин
    # --------------------
    def test_register_and_login(self):
        resp = self.client.post('/api/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'pass1234',
            'password2': 'pass1234',
            'role': 'user',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp_login = self.client.post('/api/login/', {'email': 'new@test.com', 'password': 'pass1234'})
        self.assertEqual(resp_login.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp_login.data)

    # --------------------
    # Профиль
    # --------------------
    def test_profile_get_and_update(self):
        user = User.objects.create_user('user1', 'user1@test.com', 'pass1234', first_name='User', last_name='One')
        Profile.objects.create(user=user, role='user')

        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/profile/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp_patch = self.client.patch('/api/profile/update/', {'first_name': 'John', 'last_name': 'Doe'})
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_patch.data['user']['first_name'], 'John')

    # --------------------
    # Команды
    # --------------------
    def test_team_flow(self):
        captain = User.objects.create_user('captain1', 'captain1@test.com', 'pass1234', first_name='Captain', last_name='One')
        Profile.objects.create(user=captain, role='captain')

        team = Team.objects.create(name='Team1', city='Test City', game_format='5x5', captain=captain, status='approved')

        self.client.force_authenticate(user=captain)
        resp_create = self.client.post('/api/teams/create/', {'name': 'New Team', 'city': 'New City', 'game_format': '5x5'})
        self.assertEqual(resp_create.status_code, status.HTTP_201_CREATED)

        team_id = resp_create.data['team']['id']
        resp_update = self.client.patch(f'/api/teams/{team_id}/update/', {'city': 'Updated City'})
        self.assertEqual(resp_update.status_code, status.HTTP_200_OK)

    # --------------------
    # Заявки игроков
    # --------------------
    def test_join_request_flow(self):
        player = User.objects.create_user('player1', 'player1@test.com', 'pass1234', first_name='Player', last_name='One')
        Profile.objects.create(user=player, role='player')

        captain = User.objects.create_user('captain2', 'captain2@test.com', 'pass1234', first_name='Captain', last_name='Two')
        Profile.objects.create(user=captain, role='captain')

        team = Team.objects.create(name='Team2', city='Test City', game_format='5x5', captain=captain, status='approved')

        self.client.force_authenticate(user=player)
        resp = self.client.post(f'/api/teams/{team.id}/join/', {
            'position': 'Midfielder',
            'age': 21,
            'number': 7,
            'comment': 'I want to join'
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    # --------------------
    # Турниры
    # --------------------
    def test_tournament_flow(self):
        captain = User.objects.create_user('captain3', 'captain3@test.com', 'pass1234', first_name='Captain', last_name='Three')
        Profile.objects.create(user=captain, role='captain')

        team = Team.objects.create(name='Team3', city='Test City', game_format='5x5', captain=captain, status='approved')

        organizer = User.objects.create_user('organizer1', 'organizer1@test.com', 'pass1234', first_name='Organizer', last_name='One')
        Profile.objects.create(user=organizer, role='organizer')
        OrganizerVerification.objects.create(user=organizer, organization_name='Org1', city='Test City', phone='123', experience_description='Exp', document=SimpleUploadedFile('doc.txt', b'Test'), status='approved')

        tournament = Tournament.objects.create(
            name='Tournament1', city='Test City', game_format='5x5', organizer=organizer, stadium=self.stadium,
            status='approved', start_date=timezone.now().date(), end_date=(timezone.now() + timezone.timedelta(days=1)).date(),
            confirmation_document=SimpleUploadedFile('tournament.doc', b'Test')
        )

        self.client.force_authenticate(user=captain)
        resp_apply = self.client.post(f'/api/tournaments/{tournament.id}/apply/', {'team_id': team.id, 'comment': 'We join'})
        self.assertEqual(resp_apply.status_code, status.HTTP_201_CREATED)

    # --------------------
    # Матчи
    # --------------------
    def test_match_flow(self):
        organizer = User.objects.create_user('organizer2', 'organizer2@test.com', 'pass1234', first_name='Organizer', last_name='Two')
        Profile.objects.create(user=organizer, role='organizer')
        OrganizerVerification.objects.create(user=organizer, organization_name='Org2', city='Test City', phone='123', experience_description='Exp', document=SimpleUploadedFile('doc.txt', b'Test'), status='approved')

        captain1 = User.objects.create_user('cap1', 'cap1@test.com', 'pass1234', first_name='Cap', last_name='One')
        Profile.objects.create(user=captain1, role='captain')
        team1 = Team.objects.create(name='TeamA', city='Test City', game_format='5x5', captain=captain1, status='approved')
        TournamentApplication.objects.create(team=team1, tournament=Tournament.objects.create(name='TourA', city='Test City', game_format='5x5', organizer=organizer, stadium=self.stadium, status='approved', start_date=timezone.now().date(), end_date=(timezone.now() + timezone.timedelta(days=1)).date(), confirmation_document=SimpleUploadedFile('doc2.txt', b'Test')), status='approved')

        captain2 = User.objects.create_user('cap2', 'cap2@test.com', 'pass1234', first_name='Cap', last_name='Two')
        Profile.objects.create(user=captain2, role='captain')
        team2 = Team.objects.create(name='TeamB', city='Test City', game_format='5x5', captain=captain2, status='approved')
        TournamentApplication.objects.create(team=team2, tournament=Tournament.objects.last(), status='approved')

        self.client.force_authenticate(user=organizer)
        resp_create = self.client.post('/api/matches/create/', {
            'tournament': Tournament.objects.last().id,
            'team1': team1.id,
            'team2': team2.id,
            'stadium': self.stadium.id,
            'match_date': timezone.now()
        })
        self.assertEqual(resp_create.status_code, status.HTTP_201_CREATED)

    # --------------------
    # Подписки и my-tournaments
    # --------------------
    def test_subscription_flow(self):
        user = User.objects.create_user('user2', 'user2@test.com', 'pass1234', first_name='User', last_name='Two')
        Profile.objects.create(user=user, role='user')

        organizer = User.objects.create_user('organizer3', 'organizer3@test.com', 'pass1234', first_name='Organizer', last_name='Three')
        Profile.objects.create(user=organizer, role='organizer')
        tournament = Tournament.objects.create(
            name='TourB', city='Test City', game_format='5x5', organizer=organizer, stadium=self.stadium,
            status='approved', start_date=timezone.now().date(), end_date=(timezone.now() + timezone.timedelta(days=1)).date(),
            confirmation_document=SimpleUploadedFile('doc3.txt', b'Test')
        )

        self.client.force_authenticate(user=user)
        resp_sub = self.client.post(f'/api/tournaments/{tournament.id}/subscribe/')
        self.assertIn(resp_sub.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

        resp_my = self.client.get('/api/my-tournaments/')
        self.assertEqual(resp_my.status_code, status.HTTP_200_OK)

        resp_unsub = self.client.post(f'/api/tournaments/{tournament.id}/unsubscribe/')
        self.assertEqual(resp_unsub.status_code, status.HTTP_200_OK)