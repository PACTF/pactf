#!/usr/bin/env python3

import re

__author__ = 'Yatharth Agarwal <yatharth999@gmail.com>'

INFILE = '../logs/request.log'
OUTFILE = 'same_ip.out'
LINEPAT = re.compile(r'''
    .*? 'ip', \s '(?P<ip>.+?)'
    .*? 'user_agent', \s (?P<quote1>['"]) (?P<ua>.+?) (?P=quote1)
    .*? <Competitor: \s \#(?P<competitor>\d+)
    .*? <Team: \s (?P<team>\#\d+ \s (?P<quote2>['"]) .+? (?P=quote2))
    .*?
    ''', re.VERBOSE)

map = {}

with open(INFILE) as infile:
    for line in infile.readlines():
        match = LINEPAT.match(line)
        if match:
            info = match.groupdict()

            if info['ip'] not in map:
                map[info['ip']] = {}

            if info['team'] not in map[info['ip']]:
                map[info['ip']][info['team']] = {}
                map[info['ip']][info['team']]['competitors'] = set()
                map[info['ip']][info['team']]['uas'] = set()

            map[info['ip']][info['team']]['competitors'].add(info['competitor'])
            map[info['ip']][info['team']]['uas'].add(info['ua'])

with open(OUTFILE, 'w') as outfile:
    for ip, value in map.items():
        message = "{}: ".format(ip)
        message2 = ""
        for team, data in value.items():
            competitors, uas = data['competitors'], data['uas']
            message += "{}({}) ; ".format(team, ','.join(competitors))
            message2 += "{}: {} ; ".format(team, '[' + '],['.join(uas) + ']')
        outfile.write(message + "\n" + message2 + "\n\n")
