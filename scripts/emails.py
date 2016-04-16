#!/usr/bin/env python3

__author__ = 'Yatharth Agarwal <yatharth999@gmail.com>'

from pactf import wsgi
from ctflex import models

OUTFILE = 'emails.out'

application = wsgi.application

with open(OUTFILE, 'w') as outfile:
    for competitor in models.Competitor.objects.iterator():
        if competitor.user.is_active:
            message = "{} {},{}\n".format(competitor.first_name, competitor.last_name, competitor.email)
            outfile.write(message)
            