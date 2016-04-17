#!/usr/bin/env python3

import re

__author__ = 'Yatharth Agarwal <yatharth999@gmail.com>'


INFILE = '../logs/request.log'
OUTFILE = 'team_ip.out'
LINEPAT = re.compile(r'''
    .*? 'ip', \s '(?P<ip>.+?)'
    .*? <Competitor: \s \#(?P<competitor>\d+)
    .*? <Team: \s (?P<team>\#\d+ \s '.+?')
    .*?
    ''', re.VERBOSE)

map = {}

with open(INFILE) as infile:
    for line in infile.readlines():
        match = LINEPAT.match(line)
        if match:
            info = match.groupdict()

            if info['team'] not in map:
                map[info['team']] = {}

            if info['ip'] not in map[info['team']]:
                map[info['team']][info['ip']] = set()

            map[info['team']][info['ip']].add(info['competitor'])

with open(OUTFILE, 'w') as outfile:
    for team, value in map.items():
        message = "{}: ".format(team)
        for ip, competitors in value.items():
            message += "{}({}) ; ".format(ip, ','.join(competitors))
        message += "\n"
        outfile.write(message)