from django.core.exceptions import ValidationError

from ctflex import models


def start_timer(*, team, window):
    timer = models.Timer(team=team, window=window)

    try:
        timer.save()
    except ValidationError as e:
        return False, e.messages
    else:
        return True, ""