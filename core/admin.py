from django.contrib import admin
from .models import (
    Profile,
    Team,
    TeamJoinRequest,
    Player,
    OrganizerVerification,
    Stadium,
    Tournament,
    TournamentApplication,
    TournamentSubscription,
    Match,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'city', 'email_confirmed', 'created_at')
    list_filter = ('role', 'email_confirmed', 'city')
    search_fields = ('user__username', 'user__email', 'phone', 'city')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'game_format', 'captain', 'status', 'created_at')
    list_filter = ('status', 'game_format', 'city')
    search_fields = ('name', 'city', 'captain__username')


@admin.register(TeamJoinRequest)
class TeamJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'position', 'number', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'team', 'position')
    search_fields = ('user__username', 'team__name', 'position')


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'position', 'number', 'status', 'joined_at')
    list_filter = ('status', 'team', 'position')
    search_fields = ('user__username', 'team__name', 'position')


@admin.register(OrganizerVerification)
class OrganizerVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization_name', 'city', 'phone', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'city')
    search_fields = ('user__username', 'organization_name', 'city', 'phone')


@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address', 'surface_type')
    list_filter = ('city', 'surface_type')
    search_fields = ('name', 'city', 'address')


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'game_format', 'organizer', 'stadium', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'game_format', 'city', 'stadium')
    search_fields = ('name', 'city', 'organizer__username')


@admin.register(TournamentApplication)
class TournamentApplicationAdmin(admin.ModelAdmin):
    list_display = ('team', 'tournament', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'tournament')
    search_fields = ('team__name', 'tournament__name')


@admin.register(TournamentSubscription)
class TournamentSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tournament', 'created_at')
    list_filter = ('tournament',)
    search_fields = ('user__username', 'tournament__name')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'team1', 'team2', 'stadium', 'match_date', 'status', 'score_team1', 'score_team2')
    list_filter = ('status', 'tournament', 'stadium')
    search_fields = ('tournament__name', 'team1__name', 'team2__name')