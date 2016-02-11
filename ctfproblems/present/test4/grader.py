def grade(key, submission):
    if 'flag4' in submission:
        return True, "You did it!"
    else:
        return False, "Try again…"
