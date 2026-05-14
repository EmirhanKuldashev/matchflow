from django.urls import path

from .api_views import (
    CaptainJoinRequestListAPIView,
    LoginAPIView,
    MatchCreateAPIView,
    MatchDetailAPIView,
    MatchListAPIView,
    MatchResultUpdateAPIView,
    MyTournamentsAPIView,
    OrganizerTournamentApplicationListAPIView,
    OrganizerVerificationAPIView,
    ProfileAPIView,
    RegisterAPIView,
    TeamCreateAPIView,
    TeamJoinRequestApproveAPIView,
    TeamJoinRequestCreateAPIView,
    TeamJoinRequestRejectAPIView,
    TeamListAPIView,
    TournamentApplicationApproveAPIView,
    TournamentApplicationCreateAPIView,
    TournamentApplicationRejectAPIView,
    TournamentCreateAPIView,
    TournamentDetailAPIView,
    TournamentListAPIView,
    TournamentSubscribeAPIView,
    TournamentUnsubscribeAPIView,
)

# Блок 1. API-маршруты приложения core.
# Все эти пути подключаются в config/urls.py через:
# path('api/', include('core.api_urls'))
#
# Поэтому, например:
# path('register/', ...)
# превращается в полный адрес:
# /api/register/
urlpatterns = [
    # Блок 2. API регистрации:
    # POST /api/register/
    path(
        'register/',
        RegisterAPIView.as_view(),
        name='api_register'
    ),

    # Блок 3. API входа по email:
    # POST /api/login/
    path(
        'login/',
        LoginAPIView.as_view(),
        name='api_login'
    ),

    # Блок 4. API личного кабинета:
    # GET /api/profile/
    path(
        'profile/',
        ProfileAPIView.as_view(),
        name='api_profile'
    ),

    # Блок 5. API списка подтверждённых команд:
    # GET /api/teams/
    path(
        'teams/',
        TeamListAPIView.as_view(),
        name='api_team_list'
    ),

    # Блок 6. API создания команды капитаном:
    # POST /api/teams/create/
    path(
        'teams/create/',
        TeamCreateAPIView.as_view(),
        name='api_team_create'
    ),

    # Блок 7. API подачи заявки игрока в команду:
    # POST /api/teams/<team_id>/join/
    path(
        'teams/<int:team_id>/join/',
        TeamJoinRequestCreateAPIView.as_view(),
        name='api_team_join'
    ),

    # Блок 8. API списка заявок для капитана:
    # GET /api/captain/join-requests/
    path(
        'captain/join-requests/',
        CaptainJoinRequestListAPIView.as_view(),
        name='api_captain_join_requests'
    ),

    # Блок 9. API одобрения заявки игрока:
    # POST /api/join-requests/<request_id>/approve/
    path(
        'join-requests/<int:request_id>/approve/',
        TeamJoinRequestApproveAPIView.as_view(),
        name='api_join_request_approve'
    ),

    # Блок 10. API отклонения заявки игрока:
    # POST /api/join-requests/<request_id>/reject/
    path(
        'join-requests/<int:request_id>/reject/',
        TeamJoinRequestRejectAPIView.as_view(),
        name='api_join_request_reject'
    ),

    # Блок 11. API заявки на подтверждение организатора:
    # GET  /api/organizer/verification/
    # POST /api/organizer/verification/
    path(
        'organizer/verification/',
        OrganizerVerificationAPIView.as_view(),
        name='api_organizer_verification'
    ),

    # Блок 12. API списка публичных турниров:
    # GET /api/tournaments/
    path(
        'tournaments/',
        TournamentListAPIView.as_view(),
        name='api_tournament_list'
    ),

    # Блок 13. API подробной информации о турнире:
    # GET /api/tournaments/<tournament_id>/
    path(
        'tournaments/<int:tournament_id>/',
        TournamentDetailAPIView.as_view(),
        name='api_tournament_detail'
    ),

    # Блок 14. API создания турнира:
    # POST /api/tournaments/create/
    path(
        'tournaments/create/',
        TournamentCreateAPIView.as_view(),
        name='api_tournament_create'
    ),
        # Блок 15. API подачи заявки команды на турнир:
    # POST /api/tournaments/<tournament_id>/apply/
    path(
        'tournaments/<int:tournament_id>/apply/',
        TournamentApplicationCreateAPIView.as_view(),
        name='api_tournament_apply'
    ),

    # Блок 16. API списка заявок на турниры организатора:
    # GET /api/organizer/tournament-applications/
    path(
        'organizer/tournament-applications/',
        OrganizerTournamentApplicationListAPIView.as_view(),
        name='api_organizer_tournament_applications'
    ),

    # Блок 17. API одобрения заявки команды:
    # POST /api/tournament-applications/<application_id>/approve/
    path(
        'tournament-applications/<int:application_id>/approve/',
        TournamentApplicationApproveAPIView.as_view(),
        name='api_tournament_application_approve'
    ),

    # Блок 18. API отклонения заявки команды:
    # POST /api/tournament-applications/<application_id>/reject/
    path(
        'tournament-applications/<int:application_id>/reject/',
        TournamentApplicationRejectAPIView.as_view(),
        name='api_tournament_application_reject'
    ),
        # Блок 19. API списка матчей:
    # GET /api/matches/
    path(
        'matches/',
        MatchListAPIView.as_view(),
        name='api_match_list'
    ),

    # Блок 20. API создания матча:
    # POST /api/matches/create/
    path(
        'matches/create/',
        MatchCreateAPIView.as_view(),
        name='api_match_create'
    ),

    # Блок 21. API внесения результата матча:
    # PATCH /api/matches/<match_id>/result/
    path(
        'matches/<int:match_id>/result/',
        MatchResultUpdateAPIView.as_view(),
        name='api_match_result'
    ),

    # Блок 22. API подробной информации о матче:
    # GET /api/matches/<match_id>/
    path(
        'matches/<int:match_id>/',
        MatchDetailAPIView.as_view(),
        name='api_match_detail'
    ),
        # Блок 23. API подписки на турнир:
    # POST /api/tournaments/<tournament_id>/subscribe/
    path(
        'tournaments/<int:tournament_id>/subscribe/',
        TournamentSubscribeAPIView.as_view(),
        name='api_tournament_subscribe'
    ),

    # Блок 24. API отписки от турнира:
    # POST /api/tournaments/<tournament_id>/unsubscribe/
    path(
        'tournaments/<int:tournament_id>/unsubscribe/',
        TournamentUnsubscribeAPIView.as_view(),
        name='api_tournament_unsubscribe'
    ),

    # Блок 25. API списка моих турниров:
    # GET /api/my-tournaments/
    path(
        'my-tournaments/',
        MyTournamentsAPIView.as_view(),
        name='api_my_tournaments'
    ),
]