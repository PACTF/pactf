import inspect

from django.http.response import HttpResponseNotAllowed, HttpResponse
from django.shortcuts import render, render_to_response, redirect
from django.views.generic import DetailView
from django.conf import settings

from ctf import models


# region Helpers

def get_default_dict(request):
    result = {}
    result['production'] = not settings.DEBUG
    return result


def http_method(method):
    """Decorates views to check for HTTP method"""
    assert method in ('GET', 'POST', 'PUT', 'DELETE')
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
class TeamDetailView(DetailView):
    model = models.Team
    template_name = 'ctf/team.html'

    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)
        context.update(get_default_dict(self.request))
        return context


# endregion


# region POSTs

@http_method('POST')
def grade(request, problem_id):
    # TODO(Yatharth): Implement flashing
    print("{} {}".format(problem_id, request.POST.get('flag', '')))
    return redirect('ctf:game')

# endregion
