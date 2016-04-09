"""Define template tags and filters related to sponsors"""

from django.template import Context
from django.template import loader
from django import template

register = template.Library()


class SponsorNode(template.Node):
    def __init__(self, *, nodelist):
        self.nodelist = nodelist

    def render(self, template_context):
        custom_context = Context({
            'description': self.nodelist.render(template_context)
        })
        custom_context.update(template_context)

        return loader.render_to_string(
            'ctflex/misc/sponsor.snippet.html',
            custom_context
        )


@register.tag
def sponsor(parser, token):
    """Render the sponsor template"""

    if len(token.split_contents()) > 1:
        raise template.TemplateSyntaxError(
            "{!r} tag does not take any arguments"
                .format(token.contents.split()[0])
        )

    nodelist = parser.parse(('end' + sponsor.__name__,))
    parser.delete_first_token()
    return SponsorNode(nodelist=nodelist)
