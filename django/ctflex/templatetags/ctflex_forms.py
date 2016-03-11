"""Define template tags and filters related to forms for CTFlex in production"""

from django.template import Context
from django.template.loader import get_template

from django import template

register = template.Library()


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
        template_instance = get_template(template_name='ctflex/forms/field.snippet.html')
        custom_context = Context({'field': field, 'extra_html': extra_html})
        custom_context.update(template_context)
        return template_instance.render(custom_context)


@register.tag
def formfield(parser, token):
    """Render a label, a widget, errors and extra HTML for a form field

    Usage:
        Inside a form element in a template, write

            {% formfield form.field %}<p>Whee</p>{% endformfield %}`

        This will use the form_field.html template to render the form field,
        adding `<p>Whee</p>` after the field widget. The `<p>Whee</p>` part
        is optional. The template will use the extra_group_class,
        extra_label_class, extra_input_class and extra_help_class variables
        from the context if they exist.

    Author: Yatharth
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


class NonFormFieldErrors(template.Node):
    def __init__(self, form_names):
        self.form_variables = [template.Variable(form_name) for form_name in form_names]

    def render(self, template_context):
        non_field_errors = []
        error_count = 0

        for form_variable in self.form_variables:
            try:
                form = form_variable.resolve(template_context)
            except template.VariableDoesNotExist:
                return ''

            non_field_errors.extend(form.non_field_errors())
            error_count += len(form.errors.items())

        if not error_count:
            return ''

        template_instance = get_template(template_name='ctflex/forms/non_field_errors.snippet.html')
        custom_context = {
            'non_field_errors': non_field_errors,
            'error_count': error_count,
        }
        return template_instance.render(custom_context)


@register.tag
def non_form_field_errors(parser, token):
    """Render non-field errors and a message saying there is/are error(s) for all forms passed in

    Usage:
        It's as simple as:

            {% non_form_field_errors form1 [form2 ...] %}

    Author: Yatharth
    """

    try:
        tag_name, *form_names = token.split_contents()
        if not form_names:
            raise ValueError()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires at least one argument" % token.contents.split()[0]
        )

    return NonFormFieldErrors(form_names)
