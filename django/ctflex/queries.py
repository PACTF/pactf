import importlib.machinery
import logging

from functools import partial
from os.path import join

from django.conf import settings
from django.core.exceptions import ValidationError
from django_countries.fields import Country
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from ctflex import models
from ctflex import constants

logger = logging.getLogger(constants.QUERY_LOGGER)


# General queries

def query_filter(model, **kwargs):
    return model.objects.filter(**kwargs)


def create_object(model, **kwargs):
    result = model(**kwargs)
    result.save()
    return result


def query_get(model, **kwargs):
    return model.objects.get(**kwargs)


# CTFlex-specific queries

def eligible(team):
    return not team.banned and all(competitor.country == Country('US') for competitor in team.competitor_set.all())


def get_window(window_id=None):
    return models.Window.objects.get(pk=window_id) if window_id else models.Window.objects.current()


def window_active(team):
    return team.window_active()


def viewable_problems(team, window):
    return sorted(filter(partial(problem_unlocked, team), models.CtfProblem.objects.filter(window=window)),
                  key=lambda problem: (problem.points, problem.name))


def problem_unlocked(team, problem):
    if not problem.deps:
        return True
    assert 'score' in problem.deps and 'probs' in problem.deps and iter(problem.deps['probs'])
    solves = models.Solve.objects.filter(competitor__team=team)
    filtered_score = sum(solve.problem.points for solve in solves if solve.problem.id in problem.deps['probs'])
    return filtered_score >= problem.deps['total']

# This solely exists for the purpose of rate limiting decorators
def get_team(request):
    return request.user.competitor.team

def solved(problem, team):
    return models.Solve.objects.filter(problem=problem, competitor__team=team).exists()


# TODO(Cam): Consider catching 'this' here
def create_competitor(handle, pswd, email, team):
    u = User.objects.create_user(handle, None, pswd)
    try:
        validate_password(pswd, user=u)
        c = models.Competitor(user=u, team=team, email=email)
        c.full_clean()
    except ValidationError:
        u.delete()
        logger.warning('create_competitor: Competitor creation failed: "' + handle + '".')
        raise
    else:
        c.save()
        logger.info('create_competitor: New competitor created: "' + handle + '".')
        return c


def validate_team(name, password):
    team = models.Team.objects.filter(name=name)
    if team.exists():
        if password == team[0].password:
            logger.info('validate_team: Team credentials validated for "' + name + '".')
            return team[0], 'Success!'
        logger.warning('validate_team: Team credentials incorrect for "' + name + '".')
        return None, 'Team passphrase incorrect!'
    team = models.Team(name=name, password=password)
    team.save()
    logger.info('validate_team: New team created: "' + name + '".')
    return team, 'Success!'


def board(window=None):
    return enumerate(
        sorted(
            map(lambda team: (score(team=team, window=window), team),
                filter(
                    eligible,
                    models.Team.objects.all()
                )),
            key=lambda item: item[0],
            reverse=True,
        )
    )


def grade(*, problem, flag, team):
    logger.debug(
        'grade: Grading problem ' + problem.id + ' (' + problem.name + ') for team ' + team.id +
        ' (' + team.name + ') with flag "' + flag + '".')
    if not flag:
        logger.info('grade: Flag by team ' + team.id + ' for problem ' + problem.id + ' is empty.')
        return False, "Empty flag"

    grader_path = join(settings.PROBLEMS_DIR, problem.grader)
    # XXX(Yatharth): Handle FileNotFound
    grader = importlib.machinery.SourceFileLoader('grader', grader_path).load_module()
    # extract key
    correct, message = grader.grade(hash(str(team.id) + "grading" + settings.SECRET_KEY), flag)
    logger.info('grade: Flag by team ' + team.id + ' for problem ' + problem.id + ' is ' + correct + '.')
    return correct, message


class ProblemAlreadySolvedException(Exception):
    pass


class FlagAlreadyTriedException(Exception):
    pass


def submit_flag(prob_id, competitor, flag):
    problem = models.CtfProblem.objects.get(pk=prob_id)

    # Check if the problem has already been solved
    if models.Solve.objects.filter(problem=problem, competitor__team=competitor.team).exists():
        logger.info('submit_flag: Team ' + competitor.team.id + ' has already solved problem ' + problem.id + '.')
        raise ProblemAlreadySolvedException()

    # Grade
    correct, message = grade(problem=problem, flag=flag, team=competitor.team)

    if correct:
        # This effectively updates the score too
        models.Solve(problem=problem, competitor=competitor, flag=flag).save()
        logger.info('submit_flag: Team ' + competitor.team.id + ' solved problem ' + problem.id + '.')

    # Inform the user if they had already tried the same flag
    # (This check must come after actually grading as a team might have submitted a flag
    # that later becomes correct on a problem's being updated.)
    elif models.Submission.objects.filter(problem_id=prob_id, competitor__team=competitor.team, flag=flag).exists():
        logger.info('submit_flag: Team ' + competitor.team.id +
                    ' has already tried incorrect flag "' + flag + '" for problem ' + problem.id + '.')
        raise FlagAlreadyTriedException()

    # For logging purposes, mainly
    models.Submission(p_id=problem.id, competitor=competitor, flag=flag, correct=correct).save()

    return correct, message


def score(*, team, window):
    score = 0
    for competitor in team.competitor_set.all():
        solves = competitor.solve_set.filter()
        if window is not None:
            solves = solves.filter(problem__window=window)
        for solve in solves:
            score += solve.problem.points
    return score


def get_desc(problem, team):
    if not problem.dynamic:
        return problem.description_html
    gen_path = join(settings.PROBLEMS_DIR, problem.dynamic)
    gen = importlib.machinery.SourceFileLoader('gen', gen_path).load_module()
    desc, hint = gen.generate(hash(str(team.id) + "grading" + settings.SECRET_KEY))
    return problem.process_html(desc), problem.process_html(hint)


def format_problem(problem, team):
    data = problem.__dict__
    if not problem.dynamic:
        return problem

    class Dummy:
        pass

    result = Dummy()
    data['description_html'], data['hint_html'] = queries.get_desc(problem, team)
    result.__dict__ = data
    return result
