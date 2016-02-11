"""Define template tags and filters for debugging purposes"""

from django import template

register = template.Library()


@register.filter(is_safe=True, name="str")
def str_(element):
    return str(element)


@register.filter(is_safe=True)
def pdb(element):
    import pdb
    pdb.set_trace()
    return
