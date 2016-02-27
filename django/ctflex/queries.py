import importlib.machinery
import logging
import zlib

from functools import partial
from os.path import join

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django_countries.fields import Country
from django.contrib.auth.password_validation import validate_password

from ctflex import models
from ctflex import constants

logger = logging.getLogger(constants.QUERY_LOGGER)


# TODO(Yatharth): Clean and document queries
# TODO(Yatharth): Bring back logging and set file accordingly


# region General


def get_window(window_id=None):
    return models.Window.objects.get(pk=window_id) if window_id else models.Window.objects.current()


def get_team(group, request):
    return str(request.user.competitor.team.id)


# endregion

# region Board

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
    return enumerate(
        sorted(
            map(lambda team: (score(team=team, window=window), team),
                filter(
                    _eligible,
                    models.Team.objects.all()
                )),
            key=lambda item: item[0],
            reverse=True,
        )
    )


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

def _compute_key(team):
    return zlib.adler32(bytes(str(team.id) + constants.PROBLEM_SALT + settings.SECRET_KEY, 'utf-8'))


def _grade(*, problem, flag, team):
    # logger.debug("grading {} for {} with flag {!r}".format(problem, team, flag))
    grader_path = join(settings.PROBLEMS_DIR, problem.grader)  # XXX(Yatharth): Handle FileNotFound
    grader = importlib.machinery.SourceFileLoader('grader', grader_path).load_module()

    # XXX(Yatharth): Handle no such function or signature or anything, logging appropriate error messages
    correct, message = grader.grade(_compute_key(team), flag)
    # logger.info('_grade: Flag by team ' + team.id + ' for problem ' + problem.id + ' is ' + correct + '.')
    return correct, message


class ProblemAlreadySolvedException(Exception):
    pass


class FlagAlreadyTriedException(Exception):
    pass


def submit_flag(prob_id, competitor, flag):
    problem = models.CtfProblem.objects.get(pk=prob_id)

    # Check if the problem has already been solved
    if models.Solve.objects.filter(problem=problem, competitor__team=competitor.team).exists():
        # logger.info('submit_flag: Team ' + competitor.team.id + ' has already solved problem ' + problem.id + '.')
        raise ProblemAlreadySolvedException()

    # Grade
    correct, message = _grade(problem=problem, flag=flag, team=competitor.team)

    if correct:
        # This effectively updates the score too
        models.Solve(problem=problem, competitor=competitor, flag=flag).save()
        # logger.info('submit_flag: Team ' + competitor.team.id + ' solved problem ' + problem.id + '.')

    elif not flag:
        # logger.info("empty flag for {} and {}".format(problem, team))
        message = "The flag was empty."

    # Inform the user if they had already tried the same flag
    # (This check must come after actually grading as a team might have submitted a flag
    # that later becomes correct on a problem's being updated. It must also come after the check for emptiness of flag.)
    elif models.Submission.objects.filter(problem_id=prob_id, competitor__team=competitor.team, flag=flag).exists():
        # logger.info('submit_flag: Team ' + competitor.team.id + ' has already tried incorrect flag "' + flag + '" for problem ' + problem.id + '.')
        raise FlagAlreadyTriedException()

    # For logging purposes, mainly
    models.Submission(p_id=problem.id, competitor=competitor, flag=flag, correct=correct).save()

    return correct, message


# FIXME(Yatharth): Handle such exceptions more gracefully, like use debug param in template to show faield problem names
def _get_desc(problem, team):
    if not problem.dynamic:
        return problem.description_html
    gen_path = join(settings.PROBLEMS_DIR, problem.window.code, problem.dynamic)
    gen = importlib.machinery.SourceFileLoader('gen', gen_path).load_module()
    desc, hint = gen.generate(_compute_key(team))
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
