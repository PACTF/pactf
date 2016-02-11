"""Define forms"""

from django import forms

from localflavor.us.forms import USStateField

from ctflex import models


class CompetitorForm(forms.ModelForm):

    class Meta:
        model = models.Competitor
        exclude = ()


class RegistrationForm(forms.Form):
    handle = forms.CharField(label='Username:', max_length=100)
    pswd = forms.CharField(label='Password:', widget=forms.PasswordInput())
    email = forms.EmailField(label='Email:')
    team = forms.CharField(label='Team:', max_length=80)
    team_pass = forms.CharField(label='Team passphrase:', max_length=30)
    state = USStateField(label='State')
