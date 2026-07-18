"""
URL configuration for cricportal.
"""

from django.contrib import admin
from django.urls import path

from tournament import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # Public pages
    path('', views.home, name='home'),
    path('teams/', views.teams_list, name='teams'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('players/', views.players_list, name='players'),
    path('schedule/', views.schedule, name='schedule'),
    path('results/', views.results, name='results'),
    path('points-table/', views.points_table, name='points_table'),
    path('leaderboards/', views.leaderboards, name='leaderboards'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/teams/', views.manage_teams, name='manage_teams'),
    path('dashboard/teams/add/', views.team_add, name='team_add'),
    path('dashboard/teams/<int:pk>/edit/', views.team_edit, name='team_edit'),
    path('dashboard/teams/<int:pk>/delete/', views.team_delete, name='team_delete'),
    path('dashboard/players/', views.manage_players, name='manage_players'),
    path('dashboard/players/add/', views.player_add, name='player_add'),
    path('dashboard/players/<int:pk>/edit/', views.player_edit, name='player_edit'),
    path('dashboard/players/<int:pk>/delete/', views.player_delete, name='player_delete'),
    path('dashboard/matches/', views.manage_matches, name='manage_matches'),
    path('dashboard/matches/add/', views.match_add, name='match_add'),
    path('dashboard/matches/generate/', views.generate_fixtures, name='generate_fixtures'),
    path('dashboard/matches/<int:pk>/delete/', views.match_delete, name='match_delete'),
    path('dashboard/matches/<int:pk>/result/', views.enter_result, name='enter_result'),
    path('dashboard/matches/<int:pk>/live-score/', views.live_scoring, name='live_scoring'),

    # Public pages & details
    path('match/<int:pk>/live/', views.public_live_match, name='public_live_match'),

    # API
    path('api/points-table/', views.api_points_table, name='api_points_table'),
    path('api/results/', views.api_results, name='api_results'),
    path('api/match/<int:pk>/ball/', views.api_record_ball, name='api_record_ball'),
    path('api/match/<int:pk>/status/', views.api_live_status, name='api_live_status'),
]
