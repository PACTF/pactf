"""Define competition-related template tags and filters"""

from ctflex import queries
from django import template

register = template.Library()


# region Simple Proxies to Queries

@register.simple_tag(takes_context=True)
def score(context, team):
    window = context.get('window', queries.get_window())
    return queries.score(team=team, window=window)


@register.simple_tag()
def format_problem(problem, team):
    return queries.format_problem(problem, team)


@register.simple_tag()
def solved(problem, team):
    return queries.solved(problem, team)

# endregion
