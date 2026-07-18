from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.URLField(blank=True, help_text="Optional logo image URL")
    coach_name = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def logo_or_placeholder(self):
        if self.logo:
            return self.logo
        return "https://placehold.co/80x80/0f3d2e/ffffff?text=" + (self.name[:2].upper())


class Player(models.Model):
    BATSMAN = 'Batsman'
    BOWLER = 'Bowler'
    ALLROUNDER = 'All-rounder'
    ROLE_CHOICES = [
        (BATSMAN, 'Batsman'),
        (BOWLER, 'Bowler'),
        (ALLROUNDER, 'All-rounder'),
    ]

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=BATSMAN)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    runs = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['team__name', 'name']

    def __str__(self):
        return f"{self.name} ({self.team.name})"


class Match(models.Model):
    UPCOMING = 'Upcoming'
    LIVE = 'Live'
    COMPLETED = 'Completed'
    STATUS_CHOICES = [
        (UPCOMING, 'Upcoming'),
        (LIVE, 'Live'),
        (COMPLETED, 'Completed'),
    ]

    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    match_date = models.DateTimeField()
    venue = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=UPCOMING)
    scorer = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_matches')

    class Meta:
        ordering = ['match_date']
        constraints = [
            models.CheckConstraint(condition=~models.Q(team1=models.F('team2')), name='distinct_teams'),
        ]

    def __str__(self):
        return f"{self.team1.name} vs {self.team2.name}"


class Score(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='score')
    team1_score = models.PositiveIntegerField(default=0)
    team2_score = models.PositiveIntegerField(default=0)
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_matches')

    def __str__(self):
        return f"Score: {self.match.team1.name} {self.team1_score} - {self.team2_score} {self.match.team2.name}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if not is_new:
            self._sync_points_table()

    def _sync_points_table(self):
        """Update the PointsTable for both teams whenever a score is saved."""
        match = self.match
        match.status = Match.COMPLETED
        match.save(update_fields=['status'])

        winner = self.winner

        for team in (match.team1, match.team2):
            pt, _ = PointsTable.objects.get_or_create(team=team)
            pt.matches_played += 1
            if winner is None:
                pass  # no result: no win/loss awarded
            elif winner == team:
                pt.wins += 1
                pt.points += 2
            else:
                pt.losses += 1
            pt.save()


class PointsTable(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='points')
    matches_played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-points', '-wins', 'team__name']

    def __str__(self):
        return f"{self.team.name} - {self.points} pts"

    @property
    def nrr(self):
        """Simple net-run-rate-like display placeholder (not a real NRR)."""
        if self.matches_played == 0:
            return 0.0
        return round((self.wins - self.losses) / self.matches_played, 2)


class LiveMatch(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='live_state')
    batting_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='live_battings')
    bowling_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='live_bowlings')
    
    runs = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)
    balls = models.PositiveIntegerField(default=0)  # valid balls bowled
    
    over_history = models.CharField(max_length=200, default='', blank=True)  # CSV: e.g. "0,4,W,Wd,1"
    
    striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='live_striker')
    non_striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='live_non_striker')
    current_bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='live_bowler')
    
    innings = models.PositiveIntegerField(default=1)  # 1 or 2
    team1_target = models.PositiveIntegerField(default=0)
    
    partnership_runs = models.PositiveIntegerField(default=0)
    partnership_balls = models.PositiveIntegerField(default=0)
    
    is_free_hit = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Live Match State"

    def __str__(self):
        return f"Live: {self.match.team1.name} vs {self.match.team2.name} ({self.runs}/{self.wickets})"
        
    @property
    def overs_display(self):
        overs = self.balls // 6
        balls = self.balls % 6
        return f"{overs}.{balls}"
