import datetime
import importlib
import importlib.machinery
import logging
from copy import copy
from functools import partial
from os.path import join

from django.db.models import Sum

from ctflex import constants, models
from ctflex import hashers
from ctflex import models
from ctflex import settings

logger = logging.getLogger(constants.LOGGER_NAME)


# region General

def is_competitor(user):
    return user.is_authenticated() and hasattr(user, models.Competitor.user.field.rel.name)


def get_window(codename=None):
    if codename:
        return models.Window.objects.get(codename=codename)
    else:
        return models.Window.objects.current()


def all_windows():
    return models.Window.objects.order_by('start')


def competitor_key(group, request):
    """Key function for ratelimiting based on competitor"""
    return str(request.user.competitor.id)


def solved(problem, team):
    return models.Solve.objects.filter(problem=problem, competitor__team=team).exists()


def score(*, team, window):
    score = 0
    for competitor in team.competitor_set.all():
        solves = competitor.solve_set.filter()
        if window is not None:
            solves = solves.filter(problem__window=window)
        for solve in solves:
            score += solve.problem.points
    return score


def announcements(window):
    return window.announcement_set.order_by('-date')


def unread_announcements(*, window, user):
    if not is_competitor(user):
        return 0
    return user.competitor.unread_announcements.filter(window=window)


# endregion

# region Problems List

def _is_unlocked(team, problem):
    """Compute whether a team has unlocked a problem"""

    # If a problem does not define any dependencies, it’s unlocked by default
    if problem.deps is None:
        return True

    # Extract fields
    threshold = problem.deps[constants.DEPS_THRESHOLD_FIELD]
    problems = problem.deps[constants.DEPS_PROBS_FIELD]

    # Get the list of solved problems
    solves = models.Solve.objects.filter(competitor__team=team, problem__id__in=problems)

    # (If no problems have been solved, the dependencies can’t have been met.)
    if not solves.exists():
        return False

    # Optimize for depending on solving at least one problem
    if threshold == 1:
        return True

    # Return whether the sum of the solved problems’ points exceeds the threshold
    return solves.aggregate(Sum('problem__points'))['problem__points__sum'] >= threshold


def problem_list(*, team, window):
    """Return sorted list of unlocked problems

    Problems are first sorted by points and then (case-insensitively) by their name.
    """
    unlocked_problems = (problem for problem in models.CtfProblem.objects.filter(window=window)
                         if _is_unlocked(team, problem))
    return sorted(unlocked_problems,
                  key=lambda problem: (problem.points, problem.name.lower()))


# endregion


# region Board


def _eligible_default(team):
    """Determine whether a team is eligible

    This is the function provided as a default for determining eligibility, and may be
    overridden if the `CTFLEX_ELIGIBILITY_FUNCTION` setting is set.
    """
    return not team.banned


def _get_eligible():
    """Return a reference to the eligibility function to use

    If the setting CTFLEX_ELIGIBILITY_FUNCTION if defined, it’s value as a dotted path
    to a function is used; otherwise, the default eligibility function is used.
    """

    dotted_path = settings.ELIGIBILITY_FUNCTION

    if not dotted_path:
        return _eligible_default

    module, function = dotted_path.rsplit('.', 1)

    module = importlib.import_module(module)
    return getattr(module, function)


_eligible = _get_eligible()


def _last_solve_date(*, team, window):
    """Return date of most recent Solve (or the minimum date if it doesn’t exist)"""
    solves = models.Solve.objects.filter(competitor__team=team, problem__window=window)
    if not solves.exists():
        return datetime.datetime.min
    return solves.order_by('-date').first().date


def _team_ranking_key(window, team_with_score):
    """Return key for team based on rank

    The basis for ranking is, in order, is a high scores, an old most recent solve,
    and a case-insensitively and lexicographically earlier sorted team name.
    """
    team, score_ = team_with_score
    return (
        -score_,
        _last_solve_date(team=team, window=window),
        team.name.lower(),
    )


def board(window=None):
    """Return sorted list of eligible teams with their scores"""
    eligible_teams_with_score = ((team, score(team=team, window=window))
                                 for team in models.Team.objects.iterator()
                                 if _eligible(team))
    ranked = sorted(eligible_teams_with_score, key=partial(_team_ranking_key, window))
    return ((i + 1, team, score_) for i, (team, score_) in enumerate(ranked))


# endregion


# region Problem Formatting


# XXX(Yatharth): Handle exceptions
# TODO(Yatharth): Use recommended way to import from path for Python 3.5
def _get_desc_and_hint(problem, team):
    """Return static description and hint or generate them"""

    if not problem.generator:
        return problem.description_html, problem.hint_html

    generator_path = join(settings.PROBLEMS_DIR, problem.window.codename, problem.generator)
    generator = importlib.machinery.SourceFileLoader('gen', generator_path).load_module()
    desc, hint = generator.generate(hashers.dyanamic_problem_key(team))

    return problem.process_html(desc), problem.process_html(hint)


# TODO(Yatharth): Redesign to avoid needing this function
def format_problem(problem, team):
    """Return a problem-like object, with the description and hint generated if necessary

    This function is proxied via a template tag.
    """

    if not problem.generator:
        return problem

    data = copy(problem.__dict__)

    data['description_html'], data['hint_html'] = _get_desc_and_hint(problem, team)

    return data

# endregion
