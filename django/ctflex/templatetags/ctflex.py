"""Define template tags and filters for CTFlex in production"""

from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import get_template
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


class FormFieldNode(template.Node):
    def __init__(self, *, nodelist, field_name):
        self.nodelist = nodelist
        self.field_variable = template.Variable(field_name)

    def render(self, template_context):
        try:
            field = self.field_variable.resolve(template_context)
        except template.VariableDoesNotExist:
            return ''

        extra_html = self.nodelist.render(template_context)
        template_instance = get_template(template_name='ctflex/snippets/form_field.html')
        template_context = Context({'field': field, 'extra_html': extra_html})
        return template_instance.render(template_context)


@register.tag
def formfield(parser, token):
    """Render a label, a widget and errors for a form field, optionally with extra HTML

    Usage: Inside a form element in a template, write `{% formfield form.field %}<p>Whee</p>{% endformfield %}`. This will use the form_field.html template to render the form field, adding `<p>Whee</p>` after the field widget. The `<p>Whee</p>` part is optional.
    """

    try:
        tag_name, field_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "{!r} tag requires exactly one argument"
                .format(token.contents.split()[0])
        )

    nodelist = parser.parse(('endformfield',))
    parser.delete_first_token()

    return FormFieldNode(nodelist=nodelist, field_name=field_name)

# endregion
