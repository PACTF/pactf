from functools import partial

from ctflex import models


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
    result = filter(partial(problem_unlocked, team), models.CtfProblem.objects.all())
    return map(partial(format_problem, team), result)


def problem_unlocked(team, problem):
    if not problem.deps: return True
    total = 0
    solved_probs = models.Submission.objects.filter(team=team, correct=True)
    total = sum(map(lambda s: str(s.p_id) in problem.deps['probs'], list(solved_probs)))
    return total >= problem.deps['total']


def format_problem(team, problem):
    data = problem.__dict__
    # FIXME(Yatharth): Is the first condition necessary?
    if 'dynamic' in data and not problem.dynamic:
        return problem

    class dummy:
        pass

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
