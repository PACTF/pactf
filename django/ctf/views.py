from django.shortcuts import render, render_to_response
from django.views.generic import DetailView
from django.conf import settings

from framework import models

def get_default_dict(request):
    result = {}
    result['production'] = not settings.DEBUG
    return result

def index(request):
    params = get_default_dict(request)
    # TODO(Cam): Make sure teams can view the problem before it gets put into dict; Yatharth: use a manager
    params['prob_list'] = models.CTFProblem.objects.all()
    return render(request, 'ctf/game.html', params)

class TeamDetailView(DetailView):
    model = models.Team
    template_name = 'ctf/team.html'

    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)
        context['production'] = not settings.DEBUG
        return context
