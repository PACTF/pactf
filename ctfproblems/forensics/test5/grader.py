def grade(key, submission):
    if submission.startswith('5'):
        return True, "You did it!"
    else:
        return False, "Try again…"
