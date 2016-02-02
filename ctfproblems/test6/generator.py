def generate(team):
    return 'flag{%d}' % (hash(team.name) % 10)
