import importlib
import importlib.machinery
import logging
from copy import copy
from functools import partial
from os.path import join

from django.core.cache import cache
from django.db.models import Sum
from django.utils import timezone

from ctflex import constants
from ctflex import hashers
from ctflex import models
from ctflex import settings

logger = logging.getLogger(constants.BASE_LOGGER_NAME + '.' + __name__)


# region General

def is_competitor(user):
    return user.is_authenticated() and hasattr(user, models.Competitor.user.field.rel.name)


def is_competitor_or_superuser(user):
    return user.is_superuser or is_competitor(user)


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


def solves(*, team, window=None):
    query = models.Solve.objects.filter(competitor__team=team)
    if window is not None:
        query = query.filter(problem__window=window)
    return query


def score(*, team, window):
    return (solves(team=team, window=window)
            .aggregate(score=Sum('problem__points'))['score'] or 0)


def announcements(window):
    return window.announcement_set.order_by('-date')


def unread_announcements_count(*, window, user):
    if not is_competitor(user):
        return 0
    return user.competitor.unread_announcements.filter(window=window).count()


def window_name(window):
    return window.codename if window is not None else settings.OVERALL_WINDOW_CODENAME


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

    # (If the threshold is zero, make sure all of the listed problems were solved.)
    if not threshold:
        return solves.count() == len(problems)

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
                  key=lambda problem: (problem.sort_last, problem.points, problem.name.lower()))


# endregion


# region Eligibility

# def _eligible_default(team):
#     """Determine whether a team is eligible
#
#     This is the function provided as a default for determining eligibility, and may be
#     overridden if the `CTFLEX_ELIGIBILITY_FUNCTION` setting is set.
#     """
#     return not team.banned
#
#
# def _get_eligible():
#     """Return a reference to the eligibility function to use
#
#     If the setting CTFLEX_ELIGIBILITY_FUNCTION if defined, it’s value as a dotted path
#     to a function is used; otherwise, the default eligibility function is used.
#     """
#
#     dotted_path = settings.ELIGIBILITY_FUNCTION
#
#     if not dotted_path:
#         return _eligible_default
#
#     module, function = dotted_path.rsplit('.', 1)
#
#     module = importlib.import_module(module)
#     return getattr(module, function)
#
#
# eligible = _get_eligible()

eligible = lambda team: (
    not team.banned
    and team.country == team.US_COUNTRY
    and team.background == team.SCHOOL_BACKGROUND
)


# endregion


# region Board


def _solves_in_timer(*, team, window):
    """Return 1+ solves within the team’s timer

    Implementation Notes:
      - If there was no timer, None will be returned.
    """

    if not team.has_timer(window):
        return None
    timer = team.timer(window)

    solves = models.Solve.objects.filter(
        competitor__team=team,
        problem__window=window,
        date__gte=timer.start,
        date__lte=timer.end,
    )

    if not solves.exists():
        return None

    return solves


def _score_in_timer(*, team, window):
    solves = _solves_in_timer(team=team, window=window)
    if solves is None:
        return 0
    return solves.aggregate(score=Sum('problem__points'))['score'] or 0


def _max_score(window):
    problems = window.ctfproblem_set
    if not problems.exists():
        return 0
    return problems.aggregate(score=Sum('points'))['score'] or 0


def _last_solve_in_timer_time(*, team, window):
    """Return the longest time taken to solve a problem during the team’s timer

    Implementation Notes:
    - If N/A, the maximum possible duration is returned.
    - If `window` is None, the ‘current’ window is used.
    """

    if window is None:
        window = get_window()

    solves = _solves_in_timer(team=team, window=window)

    if solves is None:
        return timezone.timedelta.max

    last_solve_date = solves.order_by('-date').first().date
    timer = team.timer(window)
    return last_solve_date - timer.start


def _team_ranking_key(window, team_with_score):
    """Return key for team based on rank

    The basis for ranking is, in order:
    - a high score
    - a short time taken since the beginning of a team’s timer to solve the
      last problem that they solved within their timer
    - a case-insensitively and lexicographically earlier sorted team name
    """
    team, score_ = team_with_score
    return (
        -score_,
        _last_solve_in_timer_time(team=team, window=window),
        team.name.lower(),
    )


def _board_cache_key(window):
    return constants.BOARD_CACHE_KEY_PREFIX + window_name(window)


def _teams_with_score_window(window):
    return (
        (team, _score_in_timer(team=team, window=window))
        for team in models.Team.objects.filter(banned=False).iterator()
    )


def _teams_with_score_overall():
    """Return teams with overall scores

    Overall scores are the sum of the normalized scores for each round.
    The normalized score for a round is 1000*(regular score)/(max possible score).
    """
    windows_with_points = [(window, _max_score(window)) for window in all_windows()]
    return (
        (
            team,
            int(settings.SCORE_NORMALIZATION * sum(
                _score_in_timer(team=team, window=window) / max_points
                for window, max_points in windows_with_points
            ))
        )
        for team in models.Team.objects.filter(banned=False).iterator()
    )


def _board_uncached(window):
    """Return sorted list of eligible teams with their scores"""

    logger.debug("computing board for {}".format(window))

    teams_with_score = _teams_with_score_window(window) if window is not None else _teams_with_score_overall()
    ranked = sorted(teams_with_score, key=partial(_team_ranking_key, window))
    board = tuple((i + 1, team, score_) for i, (team, score_) in enumerate(ranked))

    cache.set(_board_cache_key(window), board, settings.BOARD_CACHE_DURATION)
    return board


def board_cached(window=None):
    board = cache.get(_board_cache_key(window))
    if board is None:
        board = _board_uncached(window)
    else:
        logger.debug("using cache for board for {}".format(window_name(window)))
    return board


# endregion


# region Problem Formatting


def _generate_desc_and_hint(problem, team):
    """Generate description and hint for dynnamic problems"""

    assert problem.generator

    generator_path = join(settings.PROBLEMS_DIR, problem.window.codename, problem.generator)
    # TODO(Yatharth): Use recommended way to import from path for Python 3.5
    generator = importlib.machinery.SourceFileLoader('gen', generator_path).load_module()
    desc_raw, hint_raw = generator.generate(hashers.dyanamic_problem_key(team))
    desc, hint = problem.process_html(desc_raw), problem.process_html(hint_raw)

    return desc, hint


# XXX(Yatharth): Handle errors
# TODO(Yatharth): Redesign to avoid needing this function
def format_problem(problem, team):
    """Return a problem-like object, with the description and hint generated if necessary

    Usage:
        This function is proxied via a template tag.
    """

    if not problem.generator:
        return problem

    # except Exception as err:
    #     MESSAGE = "There is something wrong with this problem. Please report this to {}".format(settings.SUPPORT_EMAIL)
    #     data['description'], data['hint'] = MESSAGE, MESSAGE

    data = copy(problem.__dict__)
    data['description'], data['hint'] = _generate_desc_and_hint(problem, team)
    return data

# endregion
