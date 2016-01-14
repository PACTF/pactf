def generate(team):
    result = 'flag is flag{%d}'
    return result % (hash(team.name) % 10)
