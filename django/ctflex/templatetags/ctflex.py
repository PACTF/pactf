from django import template

register = template.Library()


# @register.simple_tag(takes_context=True)
# def ctfstatic(context, basename):
#     return '{}/{}/{}'.format(settings.PROBLEMS_STATIC_URL, context.prob.id, basename)


@register.filter(is_safe=True, name="str")
def str_(element):
    return str(element)
