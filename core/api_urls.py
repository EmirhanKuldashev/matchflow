from django.urls import path

from .api_views import (
    CaptainJoinRequestListAPIView,
    LoginAPIView,
    OrganizerVerificationAPIView,
    ProfileAPIView,
    RegisterAPIView,
    TeamCreateAPIView,
    TeamJoinRequestApproveAPIView,
    TeamJoinRequestCreateAPIView,
    TeamJoinRequestRejectAPIView,
    TeamListAPIView,
)

# Блок 1. API-маршруты приложения core.
urlpatterns = [
    # API регистрации:
    # /api/register/
    path('register/', RegisterAPIView.as_view(), name='api_register'),

    # API входа по email:
    # /api/login/
    path('login/', LoginAPIView.as_view(), name='api_login'),

    # API личного кабинета:
    # /api/profile/
    path('profile/', ProfileAPIView.as_view(), name='api_profile'),

    # API списка подтверждённых команд:
    # /api/teams/
    path('teams/', TeamListAPIView.as_view(), name='api_team_list'),

    # API создания команды капитаном:
    # /api/teams/create/
    path('teams/create/', TeamCreateAPIView.as_view(), name='api_team_create'),

    # API подачи заявки игрока в команду:
    # /api/teams/<team_id>/join/
    path(
        'teams/<int:team_id>/join/',
        TeamJoinRequestCreateAPIView.as_view(),
        name='api_team_join'
    ),

    # API списка заявок для капитана:
    # /api/captain/join-requests/
    path(
        'captain/join-requests/',
        CaptainJoinRequestListAPIView.as_view(),
        name='api_captain_join_requests'
    ),

    # API одобрения заявки игрока:
    # /api/join-requests/<request_id>/approve/
    path(
        'join-requests/<int:request_id>/approve/',
        TeamJoinRequestApproveAPIView.as_view(),
        name='api_join_request_approve'
    ),

    # API отклонения заявки игрока:
    # /api/join-requests/<request_id>/reject/
    path(
        'join-requests/<int:request_id>/reject/',
        TeamJoinRequestRejectAPIView.as_view(),
        name='api_join_request_reject'
    ),

    # API заявки на подтверждение организатора:
    # /api/organizer/verification/
    path(
        'organizer/verification/',
        OrganizerVerificationAPIView.as_view(),
        name='api_organizer_verification'
    ),
]