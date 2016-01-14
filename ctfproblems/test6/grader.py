def grade(team, flag):
    result = 'flag{%d}' % (hash(team.name) % 10)
    if result in flag:
        return True, 'It works!'
    else:
        return False, 'Darn.'
