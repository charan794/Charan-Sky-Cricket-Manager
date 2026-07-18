from tournament.models import Match, LiveMatch

def live_match_context(request):
    # Try to find a match that is currently Live
    live_match = Match.objects.filter(status=Match.LIVE).first()
    if live_match:
        try:
            live_state = live_match.live_state
            # Calculate Run Rate
            run_rate = 0.0
            if live_state.balls > 0:
                run_rate = round((live_state.runs * 6) / live_state.balls, 2)
            
            # Target calculation if 2nd innings
            target_text = ""
            if live_state.innings == 2 and live_state.team1_target > 0:
                runs_needed = live_state.team1_target - live_state.runs
                target_text = f"Needs {runs_needed} runs to win"
                
            return {
                'global_live_match': live_match,
                'global_live_state': live_state,
                'global_live_rr': run_rate,
                'global_live_target_text': target_text,
            }
        except LiveMatch.DoesNotExist:
            pass
            
    return {
        'global_live_match': None,
        'global_live_state': None,
        'global_live_rr': 0.0,
        'global_live_target_text': "",
    }
