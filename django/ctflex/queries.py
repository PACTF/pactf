from functools import partial

from django.core.exceptions import ValidationError

from ctflex import models


# General queries
def query_filter(model, **kwargs):
    return model.objects.filter(**kwargs)


def create_object(model, **kwargs):
    result = model(**kwargs)
    result.save()


def query_get(model, **kwargs):
    return model.objects.get(**kwargs)


# TODO(Cam): Consider catching 'this' here
def create_competitor(handle, pswd, email, team):
    try:
        u = models.User.objects.create_user(handle, None, pswd)
        c = models.Competitor(user=u, team=team, email=email)
        c.full_clean()
    except ValidationError:
        u.delete()
        raise
    else:
        c.save()
        return c


# CTFlex-specific queries

def get_window(window_id):
    return models.Window.objects.get(pk=window_id) if window_id else models.Window.current()


def window_active(team):
    return team.window_active()


def viewable_problems(team, window):
    result = filter(partial(problem_unlocked, team), models.CtfProblem.objects.filter(window=window))
    return map(partial(format_problem, team), result)


def problem_unlocked(team, problem):
    if not problem.deps:
        return True
    total = 0
    solved_probs = models.Submission.objects.filter(team=team, correct=True)
    total = sum(map(lambda s: str(s.p_id) in problem.deps['probs'], list(solved_probs)))
    return total >= problem.deps['total']


def format_problem(team, problem):
    data = problem.__dict__
    # XXX(Yatharth): Is the first condition necessary?
    if 'dynamic' in data and not problem.dynamic:
        return problem

    class Dummy:
        pass

    result = Dummy()
    data['description_html'] = problem.generate_desc(team)
    result.__dict__ = data
    return result


def update_score(*, competitor, problem, flag):
    # XXX(Yatharth): Use F() to avoid races?
    solve = models.Solve(competitor=competitor, problem=problem, flag=flag)
    solve.save()
