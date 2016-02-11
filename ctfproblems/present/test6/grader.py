def grade(key, flag):
    result = 'flag{%d}' % (key % 10)
    if result == flag:
        return True, 'It works!'
    else:
        return False, 'Darn.'
