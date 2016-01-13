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

def start_window(team):
    team.start_window()

def update_score(team, problem):
    # FIXME(Yatharth): Use F() to avoid races
    team.score += problem.points
    team.save()
