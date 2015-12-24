from django.shortcuts import render, render_to_response
from django.views.generic import DetailView
from django.conf import settings

from ctf import models


def get_default_dict(request):
    result = {}
    result['production'] = not settings.DEBUG
    return result


def index(request):
    return render(request, 'ctf/index.html')

def game(request):
    params = get_default_dict(request)
    # TODO(Cam): Make sure teams can view the problem before it gets put into dict
    # Yatharth: incremental revelation is for the beta; we can use a manager then
    params['prob_list'] = models.CtfProblem.objects.all
    # FIXME(yatharth): return from session or whatever shiz
    params['team'] = models.Team.objects.get(id=1)
    return render(request, 'ctf/game.html', params)

class TeamDetailView(DetailView):
    model = models.Team
    template_name = 'ctf/team.html'

    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)
        context.update(get_default_dict(self.request))
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
