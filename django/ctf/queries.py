from functools import partial

from ctf import models

# General queries
def query_filter(model, **kwargs):
    return model.objects.filter(**kwargs)

def create_object(model, **kwargs):
    result = model(**kwargs)
    result.save()

def query_get(model, **kwargs):
    return model.objects.get(**kwargs)

# CTFlex-specific queries
def window_active(team):
    return team.window_active()

def viewable_problems(team):
    result = models.CtfProblem.objects.all()
    return map(partial(format_problem, team), result)

# XXX(Cam) - this is really hacky
def format_problem(team, problem):
    data = problem.__dict__
    if 'dynamic' in data and not problem.dynamic: return problem
    class dummy: pass
    result = dummy()
    data['description_html'] = problem.generate_desc(team)
    result.__dict__ = data
    return result

def start_window(team):
    team.start_window()

def update_score(team, problem):
    # FIXME(Yatharth): Use F() to avoid races
    team.score += problem.points
    team.save()
