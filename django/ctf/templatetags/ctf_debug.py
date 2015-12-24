
from django import template

register = template.Library()

@register.filter
def pdb(element):
    import pdb; pdb.set_trace()
    return element