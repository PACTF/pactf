"""Define competition-related template tags and filters"""

from ctflex import models
from django import template

register = template.Library()


@register.simple_tag()
def team_name(team_id):
    try:
        return models.Team.objects.get(id=team_id).name
    except models.Team.DoesNotExist:
        return "ERROR"


@register.simple_tag()
def ordinal_number(rank):
    return str(rank) + {1: "st", 2: "nd", 3: "rd"}.get(
        rank if rank < 20 else rank % 10, "th")
