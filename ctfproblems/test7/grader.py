def grade(team_id, submission):
    if 'flag7' in submission:
        return True, "It works!"
    else:
        return False, "Darn."
