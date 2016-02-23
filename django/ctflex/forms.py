"""Define forms"""
import collections

from django import forms
from django.db import models as django_models
from django.contrib.auth import forms as auth_forms

from ctflex import models


# region Helpers

def _model_generated(model):
    """Generate form fields from model fields

    Usage: Decorate a form class with this decorator and set MODEL_GENERATED_FIELDS to a list of attribute name you would like to be generated.

    Drawbacks: Currently, this decorator only supports CharFields.
    """

    def decorator(cls):

        for field_name in cls.MODEL_GENERATED_FIELDS:
            model_field = model._meta.get_field(field_name)

            model_field_type = type(model_field)
            if model_field_type == django_models.CharField:
                form_field_type = forms.CharField
                attributes = {
                    ('label', 'verbose_name', None),
                    ('max_length', None, None),
                    ('min_length', None, None),
                    ('required', 'blank', lambda value: not value),
                }
            # (Maybe one day this decorator will support more types of fields.)
            else:
                raise ValueError("Unknown type of model field: {}".format(model_field_type))

            kwargs = {}
            for form_attribute, model_attribute, processor in attributes:
                if model_attribute is None:
                    model_attribute = form_attribute
                if processor is None:
                    processor = lambda value: value

                if hasattr(model_field, model_attribute):
                    kwargs[form_attribute] = processor(getattr(model_field, model_attribute))

            form_field = form_field_type(**kwargs)
            setattr(cls, field_name, form_field)

            # Register field since we're monkey-patching
            # (Django's meta-class hackery to detect fields only runs the first time the class is declared.)
            cls.base_fields[field_name] = form_field

        return cls

    return decorator


# endregion


# region Registration

class CompetitorCreationForm(forms.ModelForm):
    class Meta:
        model = models.Competitor
        fields = ('email', 'first_name', 'last_name', 'country', 'state', 'background')


class UserCreationForm(auth_forms.UserCreationForm):
    pass


class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = models.Team
        fields = ('name', 'passphrase', 'affiliation')


@_model_generated(models.Team)
class TeamJoiningForm(forms.Form):
    MODEL_GENERATED_FIELDS = ('name', 'passphrase')

    def clean_name(self):
        data = self.cleaned_data['name']
        if not models.Team.objects.filter(name=data).exists():
            raise forms.ValidationError("No team with this name exists.")
        return data

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        passphrase = cleaned_data.get('passphrase')

        if not models.Team.objects.filter(name=name, passphrase=passphrase).exists():
            # (Since clean_name checked that a team of the name existed, the passphrase must be wrong.)
            self.add_error('passphrase', "The passphrase is incorrect. Check again with your team creator.")

        return cleaned_data

# endregion
