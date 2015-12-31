def grade(team_id, submission):
    if 'flag5' in submission:
        return True, "You did it!"
    else:
        return False, "Try again…"
