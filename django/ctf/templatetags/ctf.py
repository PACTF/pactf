from django.contrib.staticfiles.templatetags.staticfiles import static
from django import template

register = template.Library()


# @register.simple_tag
# def ctfproblem_static(problem, basename):
#     static_path = "ctfproblems/{}/{}".format(problem.id, basename)
#     return static(static_path)


@register.filter(is_safe=True, name="str")
def str_(element):
    return str(element)
