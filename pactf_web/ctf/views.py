from django.shortcuts import render, render_to_response
from django.views import generic
from django.conf import settings

from ctf import models

def get_default_dict(request):
    result = {}
    result['production'] = not settings.DEBUG
    return result

def index(request):
    params = get_default_dict(request)
    # TODO - Make sure teams can view X problem before it gets put into dict
    params['prob_list'] = models.Problem.objects.all()
    return render(request, 'game.html', params)

class TeamDetailView(generic.DetailView):
    model = models.Team
    template_name = 'team.html'

    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)
        context['production'] = not settings.DEBUG
        return context
