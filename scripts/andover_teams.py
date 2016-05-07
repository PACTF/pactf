#!/usr/bin/env python3

__author__ = 'Yatharth Agarwal <yatharth999@gmail.com>'

from pactf import wsgi

application = wsgi.application

import datetime

from django.db.models import Sum

from ctflex import models
from ctflex import queries
from ctflex import settings

OUTFILE = 'andover_teams.out'
file = open(OUTFILE, 'w')

data = {}

windows_with_points = queries._windows_with_points()

teams = (models.Team.objects
         .filter(school__contains='Andover')
         .exclude(school__contains='High').all())
teams |= models.Team.objects.filter(school__contains='Phillips')

for team in teams:
    team_data = {}

    team_overall_score = queries._normalize(team=team,
                                            score_function=queries._score_in_timer,
                                            windows_with_points=windows_with_points)


    def score_function(*, team, window):
        competitor = team
        try:
            solves = (queries._solves_in_timer(team=competitor.team, window=window)
                      .filter(competitor=competitor))
        except AttributeError:
            return 0
        return solves.aggregate(score=Sum('problem__points'))['score'] or 0 if solves else 0


    for competitor in team.competitor_set.all():
        competitor_data = {}

        overall_score = queries._normalize(team=competitor, score_function=score_function,
                                           windows_with_points=windows_with_points)
        competitor_data[None] = overall_score

        for window in queries.all_windows():
            score = score_function(team=competitor, window=window)
            competitor_data[window] = score

        team_data[competitor] = competitor_data

    data[(team_overall_score, team)] = team_data

items = sorted(data.items(), key=lambda item: item[0][0], reverse=True)

file.write('\n')
file.write("Date: {}\n".format(datetime.datetime.now()))
file.write("Note: Overall score is not merely the sum of individual rounds’ scores.\n")
file.write("Note: Only solves submitted during a timer are counted.\n")
file.write('\n')

for (team_overall_score, team), competitor_data in items:

    message = "Team #{} {!r} with {}pts from {!r} (Standing: {}, Country: {}, Background: {})".format(
        team.id, team.name, team_overall_score, team.school,
        "Good" if team.standing == team.GOOD_STANDING else "Banned",
        team.country, team.background)
    file.write(message + '\n')
    file.write('=' * len(message) + '\n')
    file.write('\n')

    for competitor, window_data in competitor_data.items():
        file.write("Competitor #{} '{} {}' <{}>:\n".format(
            competitor.id, competitor.first_name, competitor.last_name, competitor.email))

        for window, score in window_data.items():
            file.write("\t{}: {}/{}\n".format(
                window.codename.title() if window else "Overall", score,
                dict(windows_with_points)[window] if window else settings.SCORE_NORMALIZATION))

        file.write('\n')
    file.write('\n')

file.close()
