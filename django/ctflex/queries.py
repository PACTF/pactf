from functools import partial

from django.core.exceptions import ValidationError

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

def get_window(window_id):
    return models.Window.objects.get(pk=window_id) if window_id else models.Window.current()


def window_active(team):
    return team.window_active()


def viewable_problems(team, window):
    return sorted(filter(partial(problem_unlocked, team), models.CtfProblem.objects.filter(window=window)),
                  key=lambda problem: (problem.points, problem.name))

def problem_unlocked(team, problem):
    if not problem.deps:
        return True

    solved_probs = models.Submission.objects.filter(team=team, correct=True)
    if 'probs' in problem.deps:
        # XXX(Yatharth): Figure out and rewrite using list comphrensions
        # XXX(Yatharth): Use score
        # total = (solve. for solve in solved_probs if str(solve.p_id) )
        total = sum(map(lambda s: str(s.p_id) in problem.deps['probs'], list(solved_probs)))
    else:
        # XXX(Yatharth): Write this
        total = 0
    return total >= problem.deps['total']


def solved(problem, team):
    return query_filter(models.Submission, problem=problem, team=team, correct=True).exists()


def update_score(*, competitor, problem, flag):
    # XXX(Yatharth): Use F() to avoid races?
    solve = models.Solve(competitor=competitor, problem=problem, flag=flag)
    solve.save()


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

# def validate_team(name, key):
#     team = models.Team.objects.filter(name=name)
#     if team.exists():
#         if key == team[0].key:
#             return team, 'Success!'
#         return None, 'Team passphrase incorrect!'
#     team = models.Team(name=name, key=key)
#     team.save()
#     return team, 'Success!'

def board(window):
    return enumerate(sorted(models.Team.objects.all(), key=lambda team: team.score(window), reverse=True))