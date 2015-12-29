import inspect

from django.http.response import HttpResponseNotAllowed, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render, render_to_response, redirect
from django.contrib import messages
from django.views.generic import DetailView
from django.conf import settings

from . import models


# region Helpers

def get_default_dict(request):
    result = {}
    result['production'] = not settings.DEBUG
    # TODO(Yatharth): Add current team ID so can link to team detail view
    return result


def http_method(method):
    """Decorates views to check for HTTP method"""
    assert method in ('GET', 'POST', 'PUT', 'DELETE')
    # TODO(Yatharth): Show custom page per http://stackoverflow.com/questions/4614294
    error = HttpResponseNotAllowed('Only {} requests allowed here'.format(method))

    def decorator(view):

        # If view is a class
        if inspect.isclass(view):
            old_get = view.get

            def new_get(self, request, *args, **kwargs):
                if request.method != method:
                    return error
                return old_get(self, request, *args, **kwargs)

            view.get = new_get

            return view

        # if view is a function
        else:
            def decorated(request, *args, **kwargs):
                if request.method != method:
                    return error
                return view(request, *args, **kwargs)

            return decorated

    return decorator


# endregion


# region GETs

@http_method('GET')
def index(request):
    if request.META.get('REQUEST_METHOD') != 'GET':
        return HttpResponseNotAllowed('Only GET allowed')

    return render(request, 'ctf/index.html')


@http_method('GET')
def game(request):
    params = get_default_dict(request)
    params['prob_list'] = models.CtfProblem.objects.all
    # TODO(yatharth): return from session or whatever shit
    params['team'] = models.Team.objects.get(id=1)
    return render(request, 'ctf/game.html', params)


@http_method('GET')
class Team(DetailView):
    model = models.Team
    template_name = 'ctf/team.html'

    def get_context_data(self, **kwargs):
        context = super(Team, self).get_context_data(**kwargs)
        context.update(get_default_dict(self.request))
        return context

@http_method('GET')
class CurrentTeam(Team):
    def get_object(self):
        # TODO(yatharth): return from session or whatever shit
        # return models.Team.objects.get(id=1)
        return models.Team.objects.get(id=1)


# endregion


# region POSTs

@http_method('POST')
def submit_flag(request, problem_id):
    # TODO(Yatharth): Update score
    # TODO(Yatharth): Disable form submission if problem already solved (and add to Feature List)
    # TODO(Cam): React if the team has already solved the problem

    flag = request.POST.get('flag', '')
    # TODO(Cam): Calculate team from session
    team = models.Team.objects.get(id=1)

    try:
        problem = models.CtfProblem.objects.get(id=problem_id)
    except models.CtfProblem.DoesNotExist:
        return HttpResponseNotFound("Problem with id {} not found".format(problem_id))
    else:
        correct, message = problem.grade(flag)
        if problem_id not in team.submissions:
            team.submissions[problem_id] = []
        if flag in team.submissions[problem_id]:
            messager = messages.error
            message = "You or someone on your team has already tried this!"
        else:
            if correct:
                messager = messages.success
                team.score += problem.points
            else:
                messager = messages.error
            team.submissions[problem_id].append(flag)
            team.save()
        messager(request, message)
        return redirect('ctf:game')

# endregion
