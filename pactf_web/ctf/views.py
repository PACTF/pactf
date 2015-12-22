from django.shortcuts import render
from django.views import generic
from django.conf import settings

from ctf import models

def get_default_dict(request):
    result = {}
    result['production'] = not settings.DEBUG
    return result

def index(request):
    params = get_default_dict(request)

class TeamDetailView(generic.DetailView):
    model = models.Team
    template_name = 'team.html'

    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)
        print(context)
