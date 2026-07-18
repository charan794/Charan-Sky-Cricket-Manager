from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Team, Player, Match, Score, PointsTable


# ---------- Authentication ----------

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        messages.error(request, "Invalid credentials. Please try again.")

    return render(request, 'tournament/login.html')


def admin_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ---------- Public pages ----------

def home(request):
    total_teams = Team.objects.count()
    total_players = Player.objects.count()
    total_matches = Match.objects.count()
    completed_matches = Match.objects.filter(status=Match.COMPLETED).count()
    upcoming_matches = Match.objects.filter(status=Match.UPCOMING).order_by('match_date')[:4]
    top_teams = PointsTable.objects.select_related('team')[:4]
    tournament_winner = _get_tournament_winner()

    context = {
        'total_teams': total_teams,
        'total_players': total_players,
        'total_matches': total_matches,
        'completed_matches': completed_matches,
        'upcoming_matches': upcoming_matches,
        'top_teams': top_teams,
        'tournament_winner': tournament_winner,
    }
    return render(request, 'tournament/home.html', context)


def teams_list(request):
    query = request.GET.get('q', '').strip()
    teams = Team.objects.all()
    if query:
        teams = teams.filter(Q(name__icontains=query) | Q(coach_name__icontains=query))
    teams = teams.prefetch_related('players')
    return render(request, 'tournament/teams.html', {'teams': teams, 'query': query})


def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    players = team.players.all()
    points = getattr(team, 'points', None)
    
    # Calculate squad aggregates
    total_runs = sum(p.runs for p in players)
    total_wickets = sum(p.wickets for p in players)
    best_batsman = players.order_by('-runs').first() if players.exists() else None
    best_bowler = players.order_by('-wickets').first() if players.exists() else None
    
    return render(request, 'tournament/team_detail.html', {
        'team': team,
        'players': players,
        'points': points,
        'total_runs': total_runs,
        'total_wickets': total_wickets,
        'best_batsman': best_batsman,
        'best_bowler': best_bowler,
    })


def players_list(request):
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    sort_by = request.GET.get('sort', '').strip()
    
    players = Player.objects.select_related('team').all()
    if query:
        players = players.filter(Q(name__icontains=query) | Q(team__name__icontains=query))
    if role_filter:
        players = players.filter(role=role_filter)
        
    if sort_by == 'runs':
        players = players.order_by('-runs')
    elif sort_by == 'wickets':
        players = players.order_by('-wickets')
        
    return render(request, 'tournament/players.html', {
        'players': players,
        'query': query,
        'role_filter': role_filter,
        'sort_by': sort_by,
    })


def schedule(request):
    status_filter = request.GET.get('status', '').strip()
    matches = Match.objects.select_related('team1', 'team2').all()
    if status_filter:
        matches = matches.filter(status=status_filter)
    return render(request, 'tournament/schedule.html', {
        'matches': matches, 'status_filter': status_filter,
    })


def results(request):
    matches = Match.objects.filter(
        status=Match.COMPLETED
    ).select_related('team1', 'team2', 'score').order_by('-match_date')
    return render(request, 'tournament/results.html', {'matches': matches})


def points_table(request):
    table = PointsTable.objects.select_related('team').all()
    tournament_winner = _get_tournament_winner()
    return render(request, 'tournament/points_table.html', {
        'table': table, 'tournament_winner': tournament_winner,
    })


def leaderboards(request):
    top_batsmen = Player.objects.select_related('team').order_by('-runs')[:5]
    top_bowlers = Player.objects.select_related('team').order_by('-wickets')[:5]
    top_allrounders = Player.objects.select_related('team').annotate(
        mvp_score=F('runs') + (F('wickets') * 20)
    ).order_by('-mvp_score')[:5]
    
    context = {
        'top_batsmen': top_batsmen,
        'top_bowlers': top_bowlers,
        'top_allrounders': top_allrounders,
    }
    return render(request, 'tournament/leaderboards.html', context)


# ---------- Dashboard (admin only) ----------

@login_required(login_url='admin_login')
def dashboard(request):
    if request.user.is_superuser:
        stats = {
            'teams': Team.objects.count(),
            'players': Player.objects.count(),
            'matches': Match.objects.count(),
            'completed': Match.objects.filter(status=Match.COMPLETED).count(),
            'upcoming': Match.objects.filter(status=Match.UPCOMING).count(),
        }
        recent_matches = Match.objects.select_related('team1', 'team2').order_by('-match_date')[:5]
    else:
        assigned = Match.objects.filter(scorer=request.user)
        stats = {
            'teams': Team.objects.count(),
            'players': Player.objects.count(),
            'matches': assigned.count(),
            'completed': assigned.filter(status=Match.COMPLETED).count(),
            'upcoming': assigned.filter(status=Match.UPCOMING).count(),
        }
        recent_matches = assigned.select_related('team1', 'team2').order_by('-match_date')[:5]
    return render(request, 'tournament/dashboard.html', {'stats': stats, 'recent_matches': recent_matches})


@login_required(login_url='admin_login')
def manage_teams(request):
    teams = Team.objects.prefetch_related('players').all()
    return render(request, 'tournament/dash_teams.html', {'teams': teams})


@login_required(login_url='admin_login')
@require_POST
def team_add(request):
    name = request.POST.get('name', '').strip()
    logo = request.POST.get('logo', '').strip()
    coach_name = request.POST.get('coach_name', '').strip()
    if name and not Team.objects.filter(name__iexact=name).exists():
        Team.objects.create(name=name, logo=logo, coach_name=coach_name)
        messages.success(request, f"Team '{name}' added.")
    else:
        messages.error(request, "Team name is required and must be unique.")
    return redirect('manage_teams')


@login_required(login_url='admin_login')
@require_POST
def team_edit(request, pk):
    team = get_object_or_404(Team, pk=pk)
    team.name = request.POST.get('name', team.name).strip()
    team.logo = request.POST.get('logo', team.logo).strip()
    team.coach_name = request.POST.get('coach_name', team.coach_name).strip()
    team.save()
    messages.success(request, f"Team '{team.name}' updated.")
    return redirect('manage_teams')


@login_required(login_url='admin_login')
@require_POST
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    name = team.name
    team.delete()
    messages.success(request, f"Team '{name}' deleted.")
    return redirect('manage_teams')


@login_required(login_url='admin_login')
def manage_players(request):
    teams = Team.objects.all()
    players = Player.objects.select_related('team').all()
    return render(request, 'tournament/dash_players.html', {'teams': teams, 'players': players})


@login_required(login_url='admin_login')
@require_POST
def player_add(request):
    name = request.POST.get('name', '').strip()
    role = request.POST.get('role', 'Batsman')
    team_id = request.POST.get('team')
    runs = int(request.POST.get('runs') or 0)
    wickets = int(request.POST.get('wickets') or 0)
    team = get_object_or_404(Team, pk=team_id)
    if name:
        Player.objects.create(name=name, role=role, team=team, runs=runs, wickets=wickets)
        messages.success(request, f"Player '{name}' added to {team.name}.")
    else:
        messages.error(request, "Player name is required.")
    return redirect('manage_players')


@login_required(login_url='admin_login')
@require_POST
def player_delete(request, pk):
    player = get_object_or_404(Player, pk=pk)
    name = player.name
    player.delete()
    messages.success(request, f"Player '{name}' deleted.")
    return redirect('manage_players')


@login_required(login_url='admin_login')
def manage_matches(request):
    from django.contrib.auth.models import User
    scorers = User.objects.filter(is_superuser=False)
    teams = Team.objects.all()
    if request.user.is_superuser:
        matches = Match.objects.select_related('team1', 'team2', 'score', 'scorer').all()
    else:
        matches = Match.objects.filter(scorer=request.user).select_related('team1', 'team2', 'score', 'scorer')
    return render(request, 'tournament/dash_matches.html', {'teams': teams, 'matches': matches, 'scorers': scorers})


@login_required(login_url='admin_login')
@require_POST
def match_add(request):
    team1_id = request.POST.get('team1')
    team2_id = request.POST.get('team2')
    match_date = request.POST.get('match_date')
    venue = request.POST.get('venue', '').strip()
    scorer_id = request.POST.get('scorer') or None
    if team1_id == team2_id:
        messages.error(request, "A team cannot play itself.")
        return redirect('manage_matches')
    team1 = get_object_or_404(Team, pk=team1_id)
    team2 = get_object_or_404(Team, pk=team2_id)
    
    # Prevents double-booking at venue (+/- 3 hours)
    from datetime import datetime, timedelta
    from django.utils.dateparse import parse_datetime
    dt = parse_datetime(match_date)
    if dt:
        overlap = Match.objects.filter(
            venue__iexact=venue,
            match_date__range=(dt - timedelta(hours=3), dt + timedelta(hours=3))
        ).exists()
        if overlap:
            messages.error(request, f"Double-booking detected! A match is already scheduled at '{venue}' within 3 hours of this slot.")
            return redirect('manage_matches')
            
    scorer = None
    if scorer_id:
        from django.contrib.auth.models import User
        scorer = get_object_or_404(User, pk=scorer_id)
        
    Match.objects.create(team1=team1, team2=team2, match_date=match_date, venue=venue, scorer=scorer)
    messages.success(request, f"Match {team1.name} vs {team2.name} scheduled.")
    return redirect('manage_matches')


@login_required(login_url='admin_login')
@require_POST
def match_delete(request, pk):
    match = get_object_or_404(Match, pk=pk)
    match.delete()
    messages.success(request, "Match deleted.")
    return redirect('manage_matches')


@login_required(login_url='admin_login')
@require_POST
def enter_result(request, pk):
    match = get_object_or_404(Match, pk=pk)
    team1_score = int(request.POST.get('team1_score') or 0)
    team2_score = int(request.POST.get('team2_score') or 0)
    winner_id = request.POST.get('winner') or None

    winner = None
    if winner_id:
        winner = get_object_or_404(Team, pk=winner_id)

    score, created = Score.objects.get_or_create(match=match)
    score.team1_score = team1_score
    score.team2_score = team2_score
    score.winner = winner
    score.save()  # triggers _sync_points_table

    messages.success(request, f"Result recorded for {match.team1.name} vs {match.team2.name}.")
    return redirect('manage_matches')


# ---------- API endpoints (Fetch API dynamic updates) ----------

def api_points_table(request):
    table = PointsTable.objects.select_related('team').all()
    data = [
        {
            'team': pt.team.name,
            'logo': pt.team.logo_or_placeholder,
            'played': pt.matches_played,
            'wins': pt.wins,
            'losses': pt.losses,
            'points': pt.points,
        }
        for pt in table
    ]
    return JsonResponse({'points_table': data})


def api_results(request):
    matches = Match.objects.filter(
        status=Match.COMPLETED
    ).select_related('team1', 'team2', 'score').order_by('-match_date')
    data = [
        {
            'id': m.pk,
            'team1': m.team1.name,
            'team2': m.team2.name,
            'team1_logo': m.team1.logo_or_placeholder,
            'team2_logo': m.team2.logo_or_placeholder,
            'team1_score': m.score.team1_score if hasattr(m, 'score') else 0,
            'team2_score': m.score.team2_score if hasattr(m, 'score') else 0,
            'winner': m.score.winner.name if hasattr(m, 'score') and m.score.winner else None,
            'venue': m.venue,
            'date': m.match_date.strftime('%b %d, %Y %H:%M'),
        }
        for m in matches
    ]
    return JsonResponse({'results': data})


# ---------- Helpers ----------

def _get_tournament_winner():
    """Return the top-ranked team if the tournament has completed matches."""
    top = PointsTable.objects.select_related('team').first()
    if top and top.matches_played > 0:
        return top.team
    return None


@login_required(login_url='admin_login')
@require_POST
def player_edit(request, pk):
    player = get_object_or_404(Player, pk=pk)
    player.name = request.POST.get('name', player.name).strip()
    player.role = request.POST.get('role', player.role)
    player.runs = int(request.POST.get('runs') or 0)
    player.wickets = int(request.POST.get('wickets') or 0)
    team_id = request.POST.get('team')
    if team_id:
        player.team = get_object_or_404(Team, pk=team_id)
    player.save()
    messages.success(request, f"Player '{player.name}' updated.")
    return redirect('manage_players')


@login_required(login_url='admin_login')
def generate_fixtures(request):
    teams = list(Team.objects.all())
    if len(teams) < 2:
        messages.error(request, "Need at least 2 teams to generate fixtures.")
        return redirect('manage_matches')
        
    num_teams = len(teams)
    has_bye = (num_teams % 2 != 0)
    if has_bye:
        teams.append(None)
        num_teams += 1
        
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    start_date = timezone.now() + timedelta(days=1)
    start_date = start_date.replace(hour=14, minute=0, second=0, microsecond=0)
    
    match_count = 0
    rounds = num_teams - 1
    
    for r in range(rounds):
        for i in range(num_teams // 2):
            t1 = teams[i]
            t2 = teams[num_teams - 1 - i]
            if t1 is not None and t2 is not None:
                match_date = start_date + timedelta(days=match_count)
                Match.objects.create(
                    team1=t1,
                    team2=t2,
                    match_date=match_date,
                    venue=f"Stadium {((match_count) % 3) + 1}",
                    status=Match.UPCOMING
                )
                match_count += 1
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        
    messages.success(request, f"Generated {match_count} fixtures successfully.")
    return redirect('manage_matches')


@login_required(login_url='admin_login')
def live_scoring(request, pk):
    if request.user.is_superuser:
        match = get_object_or_404(Match, pk=pk)
    else:
        match = get_object_or_404(Match, pk=pk, scorer=request.user)
        
    from .models import LiveMatch
    live_state, created = LiveMatch.objects.get_or_create(
        match=match,
        defaults={
            'batting_team': match.team1,
            'bowling_team': match.team2,
        }
    )
    
    if match.status == Match.UPCOMING:
        match.status = Match.LIVE
        match.save(update_fields=['status'])
        
    players_batting = Player.objects.filter(team=live_state.batting_team)
    players_bowling = Player.objects.filter(team=live_state.bowling_team)
    
    if not live_state.striker and players_batting.exists():
        live_state.striker = players_batting[0]
    if not live_state.non_striker and players_batting.count() > 1:
        live_state.non_striker = players_batting[1]
    if not live_state.current_bowler and players_bowling.exists():
        live_state.current_bowler = players_bowling[0]
    live_state.save()
    
    context = {
        'match': match,
        'live_state': live_state,
        'players_batting': players_batting,
        'players_bowling': players_bowling,
    }
    return render(request, 'tournament/live_scoring.html', context)


@login_required(login_url='admin_login')
@require_POST
def api_record_ball(request, pk):
    if request.user.is_superuser:
        match = get_object_or_404(Match, pk=pk)
    else:
        match = get_object_or_404(Match, pk=pk, scorer=request.user)
        
    from .models import LiveMatch
    live_state = get_object_or_404(LiveMatch, match=match)
    
    action = request.POST.get('action')
    value = int(request.POST.get('value') or 0)
    
    if action == 'set_striker':
        striker_id = request.POST.get('player_id')
        live_state.striker = get_object_or_404(Player, pk=striker_id)
        live_state.save()
        return JsonResponse({'state': _get_live_state_dict(live_state)})
        
    if action == 'set_non_striker':
        ns_id = request.POST.get('player_id')
        live_state.non_striker = get_object_or_404(Player, pk=ns_id)
        live_state.save()
        return JsonResponse({'state': _get_live_state_dict(live_state)})
        
    if action == 'set_bowler':
        bowler_id = request.POST.get('player_id')
        live_state.current_bowler = get_object_or_404(Player, pk=bowler_id)
        live_state.save()
        return JsonResponse({'state': _get_live_state_dict(live_state)})
        
    striker = live_state.striker
    non_striker = live_state.non_striker
    bowler = live_state.current_bowler
    
    if not striker or not bowler:
        return JsonResponse({'error': 'Please select striker and bowler first.'}, status=400)
        
    is_ball_valid = True
    history_symbol = ''
    
    if action == 'run':
        live_state.runs += value
        live_state.partnership_runs += value
        striker.runs += value
        striker.save()
        if value % 2 != 0:
            live_state.striker, live_state.non_striker = non_striker, striker
        history_symbol = str(value)
        
    elif action == 'wide':
        live_state.runs += (value + 1)
        live_state.partnership_runs += (value + 1)
        is_ball_valid = False
        history_symbol = f"{value}Wd" if value > 0 else "Wd"
        
    elif action == 'noball':
        live_state.runs += (value + 1)
        live_state.partnership_runs += (value + 1)
        striker.runs += value
        striker.save()
        is_ball_valid = False
        live_state.is_free_hit = True
        history_symbol = f"{value}Nb" if value > 0 else "Nb"
        
    elif action == 'bye':
        live_state.runs += value
        live_state.partnership_runs += value
        if value % 2 != 0:
            live_state.striker, live_state.non_striker = non_striker, striker
        history_symbol = f"{value}B"
        
    elif action == 'wicket':
        if live_state.is_free_hit:
            live_state.is_free_hit = False
            live_state.save()
            return JsonResponse({'message': 'Free Hit! Batsman cannot be dismissed.', 'state': _get_live_state_dict(live_state)})
        live_state.wickets += 1
        history_symbol = "W"
        bowler.wickets += 1
        bowler.save()
        live_state.striker = None
        live_state.partnership_runs = 0
        live_state.partnership_balls = 0
        
    if action != 'noball' and live_state.is_free_hit and is_ball_valid:
        live_state.is_free_hit = False
        
    if is_ball_valid:
        live_state.balls += 1
        live_state.partnership_balls += 1
        
    if history_symbol:
        history_list = live_state.over_history.split(',') if live_state.over_history else []
        history_list.append(history_symbol)
        live_state.over_history = ','.join(history_list)
        
    if is_ball_valid and live_state.balls % 6 == 0 and live_state.balls > 0:
        live_state.striker, live_state.non_striker = live_state.non_striker, live_state.striker
        live_state.over_history = ''
        live_state.current_bowler = None
        
    live_state.save()
    
    overs_limit = 5
    innings_over = False
    match_over = False
    
    if live_state.wickets >= 10 or (live_state.balls >= (overs_limit * 6)):
        innings_over = True
        
    if live_state.innings == 2:
        if live_state.runs >= live_state.team1_target:
            match_over = True
        elif innings_over:
            match_over = True
    elif innings_over:
        live_state.innings = 2
        live_state.team1_target = live_state.runs + 1
        live_state.batting_team, live_state.bowling_team = live_state.bowling_team, live_state.batting_team
        live_state.runs = 0
        live_state.wickets = 0
        live_state.balls = 0
        live_state.over_history = ''
        live_state.striker = None
        live_state.non_striker = None
        live_state.current_bowler = None
        live_state.partnership_runs = 0
        live_state.partnership_balls = 0
        live_state.is_free_hit = False
        live_state.save()
        return JsonResponse({
            'message': 'First Innings Complete! Innings 2 starts now.',
            'state': _get_live_state_dict(live_state)
        })
        
    if match_over:
        match.status = Match.COMPLETED
        match.save(update_fields=['status'])
        score, created = Score.objects.get_or_create(match=match)
        if live_state.innings == 2:
            if live_state.runs >= live_state.team1_target:
                score.winner = live_state.batting_team
            else:
                score.winner = live_state.bowling_team
            if match.team1 == live_state.batting_team:
                score.team1_score = live_state.runs
                score.team2_score = live_state.team1_target - 1
            else:
                score.team1_score = live_state.team1_target - 1
                score.team2_score = live_state.runs
        score.save()
        live_state.delete()
        return JsonResponse({
            'message': 'Match Finished!',
            'redirect': '/dashboard/matches/'
        })
        
    return JsonResponse({'state': _get_live_state_dict(live_state)})


def _get_live_state_dict(live_state):
    return {
        'runs': live_state.runs,
        'wickets': live_state.wickets,
        'overs': live_state.overs_display,
        'striker': live_state.striker.name if live_state.striker else None,
        'striker_id': live_state.striker.id if live_state.striker else None,
        'striker_runs': live_state.striker.runs if live_state.striker else 0,
        'non_striker': live_state.non_striker.name if live_state.non_striker else None,
        'non_striker_id': live_state.non_striker.id if live_state.non_striker else None,
        'non_striker_runs': live_state.non_striker.runs if live_state.non_striker else 0,
        'bowler': live_state.current_bowler.name if live_state.current_bowler else None,
        'bowler_id': live_state.current_bowler.id if live_state.current_bowler else None,
        'innings': live_state.innings,
        'target': live_state.team1_target,
        'over_history': live_state.over_history,
        'partnership_runs': live_state.partnership_runs,
        'partnership_balls': live_state.partnership_balls,
        'is_free_hit': live_state.is_free_hit,
        'batting_team': live_state.batting_team.name,
        'bowling_team': live_state.bowling_team.name,
    }


def api_live_status(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if match.status == Match.LIVE:
        from .models import LiveMatch
        try:
            return JsonResponse({'status': 'Live', 'data': _get_live_state_dict(match.live_state)})
        except LiveMatch.DoesNotExist:
            pass
    score_data = {}
    if hasattr(match, 'score') and match.score:
        score_data = {
            'team1_score': match.score.team1_score,
            'team2_score': match.score.team2_score,
            'winner': match.score.winner.name if match.score.winner else 'No result'
        }
    return JsonResponse({
        'status': match.status,
        'team1': match.team1.name,
        'team2': match.team2.name,
        'venue': match.venue,
        'date': match.match_date.strftime('%Y-%m-%d %H:%M'),
        'score': score_data
    })


def public_live_match(request, pk):
    match = get_object_or_404(Match, pk=pk)
    return render(request, 'tournament/public_scorecard.html', {'match': match})
