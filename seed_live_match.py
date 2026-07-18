import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cricportal.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from tournament.models import Team, Player, Match, LiveMatch

def main():
    # Find the upcoming match between Chennai Kings and Delhi Titans
    match = Match.objects.filter(team1__name='Chennai Kings', team2__name='Delhi Titans').first()
    if not match:
        print("Match not found, creating a new match...")
        team1 = Team.objects.get_or_create(name='Chennai Kings')[0]
        team2 = Team.objects.get_or_create(name='Delhi Titans')[0]
        match = Match.objects.create(
            team1=team1,
            team2=team2,
            match_date=timezone.now(),
            venue='MA Chidambaram Stadium',
            status=Match.LIVE
        )
    else:
        match.status = Match.LIVE
        match.save()
        print(f"Set match {match.pk} ({match}) to LIVE.")

    # Get players
    striker = Player.objects.filter(team=match.team1, name='Ravindra Mehra').first()
    non_striker = Player.objects.filter(team=match.team1, name='MS Dhoni Jr').first()
    bowler = Player.objects.filter(team=match.team2, name='Kuldeep Yadav').first()

    # Create/update LiveMatch state
    live_state, created = LiveMatch.objects.get_or_create(
        match=match,
        defaults={
            'batting_team': match.team1,
            'bowling_team': match.team2,
            'runs': 142,
            'wickets': 4,
            'balls': 98,
            'striker': striker,
            'non_striker': non_striker,
            'current_bowler': bowler,
            'innings': 1,
            'partnership_runs': 45,
            'partnership_balls': 32
        }
    )
    if not created:
        live_state.status = Match.LIVE
        live_state.runs = 142
        live_state.wickets = 4
        live_state.balls = 98
        live_state.striker = striker
        live_state.non_striker = non_striker
        live_state.current_bowler = bowler
        live_state.innings = 1
        live_state.partnership_runs = 45
        live_state.partnership_balls = 32
        live_state.save()
        
    print(f"Live match state updated: {live_state.runs}/{live_state.wickets} in {live_state.overs_display} overs.")

if __name__ == '__main__':
    main()
