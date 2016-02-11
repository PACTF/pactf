"""Define template tags and filters for CTFlex in production"""

from django.core.urlresolvers import reverse
from django import template

from ctflex.models import Window
from ctflex import queries

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


@register.simple_tag()
def current_window():
    return Window.objects.current()


@register.simple_tag(takes_context=True)
def other_windows(context):
    return Window.objects.other(context['window'])


# endregion


# region Complex tags

@register.simple_tag()
def switch_window(window, resolver_match):
    """Link to same 'view' but for different window"""

    if resolver_match.view_name == 'ctflex:index':
        kwargs = {
            'window_id': window.id,
        }
        # TODO(Yatharth): Extract 'ctflex:game' from here and @windows to like DEFAULT_REDIRECTING_PLACE
        return reverse('ctflex:game', kwargs=kwargs)

    kwargs = resolver_match.kwargs
    if 'window_id' in kwargs:
        kwargs['window_id'] = window.id
    return reverse(resolver_match.view_name, args=resolver_match.args, kwargs=kwargs)

# endregion
