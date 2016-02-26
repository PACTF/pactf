"""Define competition-related template tags and filters"""

from django.core.urlresolvers import reverse

from django import template

from ctflex import queries
from ctflex import constants

register = template.Library()


# region Simple Proxies

@register.simple_tag(takes_context=True)
def score(context, team):
    return queries.score(team=team, window=context['window'])


@register.simple_tag()
def format_problem(problem, team):
    return queries.format_problem(problem, team)


@register.simple_tag()
def solved(problem, team):
    return queries.solved(problem, team)


# endregion


# region More Complex Tags

@register.simple_tag(takes_context=True)
def switch_window(context, window):
    """Compute link URL to the same 'view' but for a different window

    Usage:
        In a template rendered by some View X, you can link to a page also rendered by view X but for a different window, Window Y, as follows:

            <a href="{% switch_window <Window Y> resolver_match=request.resolver_match %}">Go to Window Y!</a>

    Implementation:
        All of the parameters passed to View X are included in the URL to View X for Window Y. If View X takes `window_id` as a named parameter, that will be changed to the ID of Window Y. Otherwise (if View X does not take `window_id` as a parameter), the view associated with `WINDOW_CHANGE_URL` will be used instead, being passed just `window_id`.
    """

    resolver_match = context['request'].resolver_match

    if 'window_id' in resolver_match.kwargs:
        kwargs = resolver_match.kwargs
        args = resolver_match.args
        view_name = resolver_match.view_name
    else:
        kwargs = {}
        args = []
        view_name = constants.WINDOW_CHANGE_URL

    kwargs['window_id'] = window.id
    return reverse(view_name, args=args, kwargs=kwargs)

# endregion
