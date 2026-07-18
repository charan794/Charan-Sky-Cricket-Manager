"""Seed script: create superuser, teams, players, matches, and results."""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cricportal.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from datetime import timedelta

from tournament.models import Team, Player, Match, Score, PointsTable

# --- Superuser ---
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@skycharan.com', 'admin123')
    print("Superuser created: admin / admin123")
else:
    print("Superuser already exists")

# --- Teams ---
teams_data = [
    ('Mumbai Lions', 'https://placehold.co/80x80/1e40af/ffffff?text=ML', 'Rahul Sharma'),
    ('Chennai Kings', 'https://placehold.co/80x80/b45309/ffffff?text=CK', 'Stephen Fleming'),
    ('Bengaluru Blasters', 'https://placehold.co/80x80/dc2626/ffffff?text=BB', 'Mike Hesson'),
    ('Delhi Titans', 'https://placehold.co/80x80/1e3a8a/ffffff?text=DT', 'Ricky Ponting'),
]
teams = {}
for name, logo, coach in teams_data:
    obj, created = Team.objects.get_or_create(name=name, defaults={'logo': logo, 'coach_name': coach})
    teams[name] = obj
    print(f"{'Created' if created else 'Exists'}: {name}")

# --- Players ---
players_data = [
    ('Rohit Verma', 'Batsman', 'Mumbai Lions', 845, 3),
    ('Jaspreet Kumar', 'Bowler', 'Mumbai Lions', 120, 22),
    ('Surya Patel', 'All-rounder', 'Mumbai Lions', 410, 8),
    ('MS Dhoni Jr', 'Batsman', 'Chennai Kings', 720, 2),
    ('Deepak Singh', 'Bowler', 'Chennai Kings', 95, 18),
    ('Ravindra Mehra', 'All-rounder', 'Chennai Kings', 350, 11),
    ('Virat Anand', 'Batsman', 'Bengaluru Blasters', 910, 1),
    ('Mohammed Aamir', 'Bowler', 'Bengaluru Blasters', 80, 25),
    ('Glenn Thomas', 'All-rounder', 'Bengaluru Blasters', 480, 6),
    ('Shikhar Rana', 'Batsman', 'Delhi Titans', 680, 0),
    ('Kuldeep Yadav', 'Bowler', 'Delhi Titans', 60, 20),
    ('Hardik Joshi', 'All-rounder', 'Delhi Titans', 390, 9),
]
for name, role, team_name, runs, wickets in players_data:
    obj, created = Player.objects.get_or_create(
        name=name, team=teams[team_name],
        defaults={'role': role, 'runs': runs, 'wickets': wickets}
    )
    print(f"{'Created' if created else 'Exists'}: {name} ({team_name})")

# --- Matches ---
now = timezone.now()
matches_data = [
    ('Mumbai Lions', 'Chennai Kings', now - timedelta(days=6), 'Wankhede Stadium'),
    ('Bengaluru Blasters', 'Delhi Titans', now - timedelta(days=4), 'M. Chinnaswamy Stadium'),
    ('Mumbai Lions', 'Bengaluru Blasters', now - timedelta(days=2), 'Eden Gardens'),
    ('Chennai Kings', 'Delhi Titans', now + timedelta(days=1), 'MA Chidambaram Stadium'),
    ('Mumbai Lions', 'Delhi Titans', now + timedelta(days=3), 'Arun Jaitley Stadium'),
    ('Chennai Kings', 'Bengaluru Blasters', now + timedelta(days=5), 'Wankhede Stadium'),
]
matches = []
for t1, t2, date, venue in matches_data:
    obj, created = Match.objects.get_or_create(
        team1=teams[t1], team2=teams[t2], match_date=date,
        defaults={'venue': venue, 'status': 'Upcoming'}
    )
    matches.append(obj)
    print(f"{'Created' if created else 'Exists'}: {t1} vs {t2} @ {venue}")

# --- Results for completed matches ---
results_data = [
    (0, 185, 172, 'Mumbai Lions'),   # Mumbai Lions won
    (1, 198, 201, 'Delhi Titans'),   # Delhi Titans won
    (2, 210, 188, 'Mumbai Lions'),   # Mumbai Lions won
]
for idx, s1, s2, winner_name in results_data:
    m = matches[idx]
    if m.status == 'Completed':
        print(f"Result exists: {m.team1.name} vs {m.team2.name}")
        continue
    score, created = Score.objects.get_or_create(match=m)
    score.team1_score = s1
    score.team2_score = s2
    score.winner = teams[winner_name]
    score.save()
    print(f"Result recorded: {m.team1.name} {s1} - {s2} {m.team2.name} -> {winner_name} won")

print("\n=== Seed complete ===")
print("Login: admin / admin123")
print(f"Teams: {Team.objects.count()}, Players: {Player.objects.count()}, Matches: {Match.objects.count()}")
pt = PointsTable.objects.all().order_by('-points')
for p in pt:
    print(f"  {p.team.name}: {p.matches_played}P {p.wins}W {p.losses}L {p.points}pts")
