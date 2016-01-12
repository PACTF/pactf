from ctf import models

# General queries
def query_filter(model, **kwargs):
    return model.objects.get(**kwargs)

def create_object(model, **kwargs):
    result = model(**kwargs)
    result.save()

# CTFlex-specific queries
def window_active(team):
    return team.window_active()

def start_window(team):
    team.start_window()

def update_score(team, points):
    team.score += points
    team.save()
