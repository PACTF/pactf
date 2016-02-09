from functools import partial

from django.core.exceptions import ValidationError
from django_countries.fields import Country

from ctflex import models


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
    return not team.banned and team.country == Country('us')

def get_window(window_id):
    return models.Window.objects.get(pk=window_id) if window_id else models.Window.objects.current()


def window_active(team):
    return team.window_active()


def viewable_problems(team, window):
    return sorted(filter(partial(problem_unlocked, team), models.CtfProblem.objects.filter(window=window)),
                  key=lambda problem: (problem.points, problem.name))

def problem_unlocked(team, problem):
    if not problem.deps:
        return True
    assert 'total' in problem.deps and 'probs' in problem.deps and iter(problem.deps['probs'])
    solves = models.Solve.objects.filter(competitor__team=team)
    filtered_score = sum(solve.problem.points for solve in solves if solve.problem.id in problem.deps['probs'])
    return filtered_score >= problem.deps['total']


def solved(problem, team):
    return models.Solve.objects.filter(problem=problem, competitor__team=team).exists()

# TODO(Cam): Consider catching 'this' here
def create_competitor(handle, pswd, email, team):
    u = models.User.objects.create_user(handle, None, pswd)
    try:
        c = models.Competitor(user=u, team=team, email=email)
        c.full_clean()
    except ValidationError:
        u.delete()
        raise
    else:
        c.save()
        return c

def validate_team(name, key):
    team = models.Team.objects.filter(name=name)
    if team.exists():
        if key == team[0].password:
            return team[0], 'Success!'
        return None, 'Team passphrase incorrect!'
    team = models.Team(name=name, key=key)
    team.save()
    return team, 'Success!'



def board(window):
    return enumerate(
        sorted(
            filter(
                eligible,
                models.Team.objects.all()
            ),
            key=lambda team: score(team=team, window=window),
            reverse=True,
        )
    )


class ProblemAlreadySolvedException(Exception):
    pass

class FlagAlreadyTriedException(Exception):
    pass


# TODO: Test all these cases
def submit_flag(prob_id, competitor, flag):
    problem = models.CtfProblem.objects.get(pk=prob_id)

    if models.Solve.objects.filter(problem=problem, competitor=competitor).exists():
        raise ProblemAlreadySolvedException()
    elif models.Submission.objects.filter(problem_id=prob_id, team=competitor.team, flag=flag).exists():
        raise FlagAlreadyTriedException()

    # Grade
    correct, message = problem.grade(flag=flag, team=competitor.team)

    if correct:
        # This effectively updates the score too
        models.Solve(problem=problem, competitor=competitor, flag=flag).save()

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