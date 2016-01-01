from django import template

register = template.Library()

@register.filter(is_safe=True)
def pdb(element):
    import pdb; pdb.set_trace()
    return element