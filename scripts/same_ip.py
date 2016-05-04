#!/usr/bin/env python3

import re

__author__ = 'Yatharth Agarwal <yatharth999@gmail.com>'

INFILE = '../logs/request.log'
OUTFILE = 'same_ip.out'
LINEPAT = re.compile(r'''
    .*? 'ip', \s '(?P<ip>.+?)'
    .*? <Competitor: \s \#(?P<competitor>\d+)
    .*? <Team: \s (?P<team>\#\d+ \s (?P<quote>['"]) .+? (?P=quote))
    .*?
    ''', re.VERBOSE)

map = {}

with open(INFILE) as infile:
    for line in infile.readlines():
        match = LINEPAT.match(line)
        if match:
            info = match.groupdict()
            info['team'] = info['team']
            info['competitor'] = info['competitor']

            if info['ip'] not in map:
                map[info['ip']] = {}

            if info['team'] not in map[info['ip']]:
                map[info['ip']][info['team']] = set()

            map[info['ip']][info['team']].add(info['competitor'])

with open(OUTFILE, 'w') as outfile:
    for ip, value in map.items():
        message = "{}: ".format(ip)
        for team, competitors in value.items():
            message += "{}({}) ; ".format(team, ','.join(competitors))
        message += "\n"
        outfile.write(message)
