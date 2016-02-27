def grade(key, submission):
    if 'flag7' in submission:
        return True, "It works!"
    else:
        return False, "Darn."
