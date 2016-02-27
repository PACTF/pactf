import importlib.machinery
import logging
from functools import partial
from os.path import join

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from django_countries.fields import Country

from ctflex import constants
from ctflex import hashers
from ctflex import models

logger = logging.getLogger(constants.QUERY_LOGGER)


# TODO(Yatharth): Clean and document queries
# TODO(Yatharth): Bring back logging and set file accordingly


# region General


def get_window(window_codename=None):
    return models.Window.objects.get(codename=window_codename) if window_codename else models.Window.objects.current()


def competitor_key(group, request):
    """Key function for ratelimiting based on competitor"""
    return str(request.user.competitor.team.id)


# endregion

# region Game

# FIXME(Yatharth): Test unlocking
def _problem_unlocked(team, problem):
    """Check if a team has unlocked a problem

    Refer to the README for the specification.
    """

    if problem.deps is None:
        return True

    threshold = problem.deps[constants.DEPS_THRESHOLD_FIELD]
    problems = problem.deps[constants.DEPS_PROBS_FIELD]

    solves = models.Solve.objects.filter(competitor__team=team, problem__id__in=problems)

    if not solves.exists():
        return False

    # Just an optimization
    if score == 1:
        return True

    return solves.aggregate(Sum('problem__points'))['problem__points__sum'] >= threshold


def viewable_problems(team, window):
    return sorted(filter(partial(_problem_unlocked, team), models.CtfProblem.objects.filter(window=window)),
                  key=lambda problem: (problem.points, problem.name.lower()))


# endregion

# region Template Tag

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


# endregion

# region Board


def _eligible(team):
    return not team.banned and all(
        competitor.country == Country('US') and competitor.background == models.Competitor.HIGHSCHOOL
        for competitor in team.competitor_set.all()
    )


def board(window=None):
    teams = (team for team in models.Team.objects.iterator() if _eligible(team))
    decorated = ((score(team=team, window=window), team.name, team) for team in teams)
    sorted_ = sorted(decorated, reverse=True)
    enumerated = ((i + 1, team, score_) for i, (score_, name, team) in enumerate(sorted_))
    return enumerated


# endregion

# region Auth

def create_competitor(handle, pswd, email, team, state):
    user = settings.AUTH_USER_MODEL.objects.create_user(handle, None, pswd)
    try:
        validate_password(pswd, user=user)
        competitor = models.Competitor(user=user, team=team, email=email, state=state, first_name="dummy",
                                       last_name="dummy")
        competitor.full_clean()


    except ValidationError:
        user.delete()
        # logger.warning('create_competitor: Competitor creation failed: {}'.format(handle))
        raise
    else:
        competitor.save()
        # logger.info('create_competitor: New competitor created: {}'.format(handle))
        return competitor


def validate_team(name, password):
    team = models.Team.objects.filter(name=name)
    if team.exists():
        if password == team[0].password:
            # logger.info('validate_team: Team credentials validated for "' + name + '".')
            return team[0], 'Success!'
        # logger.warning('validate_team: Team credentials incorrect for "' + name + '".')
        return None, 'Team passphrase incorrect!'
    team = models.Team(name=name, password=password)
    team.save()
    # logger.info('validate_team: New team created: "' + name + '".')
    return team, 'Success!'


# endregion Auth

# region Game


# FIXME(Yatharth): Handle such exceptions more gracefully, like use debug param in template to show faield problem names
def _get_desc(problem, team):
    if not problem.dynamic:
        return problem.description_html
    gen_path = join(settings.PROBLEMS_DIR, problem.window.codename, problem.dynamic)
    gen = importlib.machinery.SourceFileLoader('gen', gen_path).load_module()
    desc, hint = gen.generate(hashers.dyanamic_problem_key(team))
    return problem.process_html(desc), problem.process_html(hint)


# TODO(Yatharth): Improve design
def format_problem(problem, team):
    data = problem.__dict__
    if not problem.dynamic:
        return problem

    class Dummy:
        pass

    result = Dummy()

    data['description_html'], data['hint_html'] = _get_desc(problem, team)
    result.__dict__ = data
    return result

    # endregion
