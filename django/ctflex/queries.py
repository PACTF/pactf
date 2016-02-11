import importlib.machinery
from functools import partial
from os.path import join

from django.conf import settings
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
    return not team.banned and team.country == Country('US')

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
    if not flag:
        return False, "Empty flag"

    grader_path = join(settings.PROBLEMS_DIR, problem.grader)
    # XXX(Yatharth): Handle FileNotFound
    grader = importlib.machinery.SourceFileLoader('grader', grader_path).load_module()
    # extract key
    correct, message = grader.grade(hash(str(team.id) + "grading" + settings.SECRET_KEY), flag)
    return correct, message


class ProblemAlreadySolvedException(Exception):
    pass

class FlagAlreadyTriedException(Exception):
    pass


def submit_flag(prob_id, competitor, flag):
    problem = models.CtfProblem.objects.get(pk=prob_id)

    # Check if the problem has already been solved
    if models.Solve.objects.filter(problem=problem, competitor__team=competitor.team).exists():
        raise ProblemAlreadySolvedException()

    # Grade
    correct, message = grade(problem=problem, flag=flag, team=competitor.team)

    if correct:
        # This effectively updates the score too
        models.Solve(problem=problem, competitor=competitor, flag=flag).save()

    # Inform the user if they had already tried the same flag
    # (This check must come after actually grading as a team might have submitted a flag that later becomes correct on a problem's being updated.)
    elif models.Submission.objects.filter(problem_id=prob_id, competitor__team=competitor.team, flag=flag).exists():
            raise FlagAlreadyTriedException()

    # For logging purposes, mainly
    models.Submission(p_id=problem.id, competitor=competitor, flag=flag, correct=correct).save()

    return correct, message


def score(*, team, window):
    score = 0
    print(team)
    for competitor in team.competitor_set.all():
        solves = competitor.solve_set.filter()
        print(competitor)
        if window is not None:
            solves = solves.filter(problem__window=window)
        for solve in solves:
            print(solve.problem.id)
            score += solve.problem.points
            print(score)
    return score


def get_desc(problem, team):
    if not problem.dynamic:
        return problem.description_html
    gen_path = join(settings.PROBLEMS_DIR, problem.dynamic)
    gen = importlib.machinery.SourceFileLoader('gen', gen_path).load_module()
    desc = gen.generate(hash(str(team.id) + "grading" + settings.SECRET_KEY))
    return problem.process_html(desc)