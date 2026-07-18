from django.contrib import admin

from .models import Team, Player, Match, Score, PointsTable


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 1


class ScoreInline(admin.StackedInline):
    model = Score
    extra = 0
    readonly_fields = ('winner_display',)

    def winner_display(self, obj):
        return obj.winner.name if obj.winner else "—"
    winner_display.short_description = "Winner"


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'coach_name', 'player_count')
    search_fields = ('name', 'coach_name')
    inlines = [PlayerInline]

    def player_count(self, obj):
        return obj.players.count()
    player_count.short_description = "Players"


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'team', 'runs', 'wickets')
    list_filter = ('role', 'team')
    search_fields = ('name',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('team1', 'team2', 'match_date', 'venue', 'status')
    list_filter = ('status', 'venue')
    search_fields = ('team1__name', 'team2__name', 'venue')
    inlines = [ScoreInline]


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('match', 'team1_score', 'team2_score', 'winner')
    search_fields = ('match__team1__name', 'match__team2__name')


@admin.register(PointsTable)
class PointsTableAdmin(admin.ModelAdmin):
    list_display = ('team', 'matches_played', 'wins', 'losses', 'points')
    list_display_links = ('team',)
    ordering = ('-points', '-wins')
