# SkyCharan Tournament System — Cricket Tournament Management System

A full-stack web application for managing cricket tournaments, built with **Django** (backend) and **HTML/CSS/JavaScript** (frontend).

## Features

- **Authentication**: Admin login/logout system; only admins can access the dashboard.
- **Team Management**: Add, edit, and delete teams (name, logo, coach).
- **Player Management**: Add players to teams with roles (Batsman / Bowler / All-rounder), runs, and wickets.
- **Match Scheduling**: Schedule matches between two teams with date and venue.
- **Match Results**: Enter scores and winner; the points table updates automatically.
- **Auto Points Table**: Win = 2 points, Loss = 0 points. Standings update instantly when a result is saved.
- **Public Pages**: Home, Teams, Players, Match Schedule, Results, Points Table.
- **Dynamic Updates**: Fetch API powers refresh-without-reload on Results and Points Table pages.
- **Search & Filter**: Search teams/players; filter matches by status (Upcoming/Completed).
- **Tournament Winner**: The top-ranked team is highlighted as tournament champion.
- **Modern UI**: Dark + green glassmorphism theme with hover animations, responsive design.

## Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Backend  | Django 5+ (Python)                  |
| Database | SQLite (default; swap to Postgres for production) |
| Frontend | HTML, CSS (glassmorphism), Vanilla JS (Fetch API) |
| Server   | Gunicorn (production)               |

## Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Seed sample data (creates superuser + teams + players + matches)
python seed_data.py

# 4. Start the dev server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

### Admin Credentials (from seed)

- **Username**: `admin`
- **Password**: `admin123`

> Change these credentials in production.

## Project Structure

```
cricportal/              # Django project settings
  settings.py
  urls.py
tournament/              # Main application
  models.py             # Team, Player, Match, Score, PointsTable
  views.py              # Auth, public pages, dashboard CRUD, API
  admin.py              # Admin panel configuration
  urls.py               # URL routing (app-level)
  templates/tournament/  # All HTML templates
    base.html           # Shared layout + navbar
    home.html
    teams.html
    team_detail.html
    players.html
    schedule.html
    results.html
    points_table.html
    login.html
    dashboard.html
    dash_teams.html
    dash_players.html
    dash_matches.html
  static/tournament/
    css/style.css       # Dark + green glassmorphism theme
    js/main.js          # Navbar toggle, message auto-dismiss
    js/results.js       # Fetch API dynamic results
    js/points.js        # Fetch API dynamic points table
manage.py
seed_data.py            # Sample data seeding script
requirements.txt
render.sh               # Deployment entry point
Procfile
render.yaml
```

## Models

- **Team**: name, logo (URL), coach_name
- **Player**: name, role (Batsman/Bowler/All-rounder), team (FK), runs, wickets
- **Match**: team1 (FK), team2 (FK), match_date, venue, status (Upcoming/Completed)
- **Score**: match (OneToOne), team1_score, team2_score, winner (FK to Team)
- **PointsTable**: team (OneToOne), matches_played, wins, losses, points

### Points Table Auto-Logic

When a match result is saved via `Score.save()`:
1. Match status is set to `Completed`.
2. For each team in the match: `matches_played` increments.
3. The winner gets `wins += 1` and `points += 2`.
4. The loser gets `losses += 1`.

## API Endpoints (Fetch API)

| Endpoint               | Method | Description                    |
|------------------------|--------|--------------------------------|
| `/api/points-table/`   | GET    | JSON of current standings       |
| `/api/results/`        | GET    | JSON of completed match results |

## Deployment (Render)

1. Push this repo to GitHub.
2. Create a new Web Service on [Render](https://render.com).
3. Use the included `render.yaml` or set:
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `sh render.sh`
4. Set `SECRET_KEY` and `DEBUG=0` as environment variables for production.

## Django Admin Panel

The built-in Django admin is available at `/admin/` with the superuser credentials above. It provides full CRUD for all models with inline editing for players and scores.
