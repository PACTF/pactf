#!/usr/bin/python3

ips = {}
for line in open('logs.txt'):
    prob, ip = line.split(' - ')
    ip = eval(ip)[0]
    if ip not in ips:
        ips[ip] = [prob]
    else:
        ips[ip].append(prob)

for team in open('ips.txt'):
    if not team: continue
    data = team.split('; ')
    ip = data[0]
    team = data[1:]
    if ip not in ips:
        print('Team(s) %s did not access server.' % team)
        continue
    print('Team(s) %s solved problems %s' % (team, ips[ip]))

