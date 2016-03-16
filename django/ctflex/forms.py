"""Define forms to be used by views"""

from django import forms
from django.db import models as django_models
from django.contrib.auth import forms as auth_forms

from ctflex import models


# region Helpers

def _model_generated(model):
    """Generate form fields from model fields

    Purpose:
        This decorator lets you have form field attributes like
        `max_length` copied over from a model field while being DRY.

    Usage:
        Decorate a form class with this decorator and set MODEL_GENERATED_FIELDS
        to a list of attribute names you would like to be generated.

    Limitations:
        - Currently, this decorator only supports CharFields.

    Author: Yatharth
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
            else:
                # (Maybe one day this decorator will support more types of fields.)
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
    prefix = 'competitor'

    class Meta:
        model = models.Competitor
        fields = ('email', 'first_name', 'last_name')


class UserCreationForm(auth_forms.UserCreationForm):
    """Subclass UserCreationForm and monkey-patch some fields

    This class is different from its superclass in these ways:
    - Password confirmation is not required.
    - Help text for fields is not displayed.
    """
    prefix = 'user'

    def __init__(self, *args, data=None, **kwargs):
        # Copy `password2`’s value to `password1`
        if data is not None:
            # Make a copy as `data` might not be mutable
            data = data.copy()

            data['{}-password1'.format(self.prefix)] = data.get('{}-password2'.format(self.prefix), '')

        super().__init__(*args, data=data, **kwargs)

        self.fields['password2'].label = self.fields['password1'].label
        self.fields['password2'].help_text = ''
        self.fields['username'].help_text = ''


class TeamCreationForm(forms.ModelForm):
    prefix = 'new_team'

    class Meta:
        model = models.Team
        fields = ('name', 'passphrase', 'affiliation', 'country', 'background')


@_model_generated(models.Team)
class TeamJoiningForm(forms.Form):
    prefix = 'existing_team'

    MODEL_GENERATED_FIELDS = ('name', 'passphrase')

    def clean_name(self):
        data = self.cleaned_data['name']

        if not models.Team.objects.filter(name=data).exists():
            raise forms.ValidationError("No team with this name exists.")

        return data

    def clean(self):
        """Check if the name and passphrase is correct"""

        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        passphrase = cleaned_data.get('passphrase')

        if not models.Team.objects.filter(name=name, passphrase=passphrase).exists():
            # (Since clean_name checked that a team of the name existed,
            #  it must be the passphrase that is wrong.)
            self.add_error('passphrase', "The passphrase is incorrect. Check again with your team creator.")

        return cleaned_data

    def save(self):
        """Return a reference to the team"""
        return models.Team.objects.get(name=self.cleaned_data['name'], passphrase=self.cleaned_data['passphrase'])

# endregion
