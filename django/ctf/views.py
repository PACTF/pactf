import inspect
import datetime
from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.http.response import HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.conf import settings

from ctf import models, queries


# region Helper Methods

def is_competitor(user):
    return user.is_authenticated() and hasattr(user, models.Competitor.user.field.rel.name)


def get_default_dict(request):
    result = {}
    result['production'] = not settings.DEBUG
    team = request.user.competitor.team if is_competitor(request.user) else None
    result['team'] = team
    result['problems_viewable'] = team.can_view_problems() if team else False
    return result


# endregion


# region Decorators

def universal_decorator(methodname):
    """Makes a decorator factory able to decorate both a function and a certain method of a class

    This meta-decorator factory does NOT work on non-factory decorators (decorators that do not take arguments). Make your decorator (factory) take no arguments if you must.

    For help, contact Yatharth."""

    def meta_decorator_factory(old_decorator_factory):

        def new_decorator_factory(*args, **kwargs):
            old_decorator = old_decorator_factory(*args, **kwargs)

            @wraps
            def new_decorator(view):
                if inspect.isclass(view):
                    decorator = method_decorator(old_decorator, methodname)
                else:
                    decorator = old_decorator
                return decorator(view)

            return new_decorator

        return new_decorator_factory

    return meta_decorator_factory


@universal_decorator(methodname='get')
def single_http_method(method):
    """Decorates views to check for HTTP method"""

    assert method in ('GET', 'POST', 'PUT', 'DELETE')
    # TODO(Yatharth): Show custom page per http://stackoverflow.com/questions/4614294
    error = HttpResponseNotAllowed('Only {} requests allowed here'.format(method))

    def decorator(view):
        def decorated(request, *args, **kwargs):
            if request.method != method:
                return error
            return view(request, *args, **kwargs)

        return decorated

    return decorator


@universal_decorator(methodname='dispatch')
def competitors_only():
    return user_passes_test(is_competitor)


# endregion


# region GETs

@single_http_method('GET')
def index(request):
    return render(request, 'ctf/index.html', get_default_dict(request))


@single_http_method('GET')
@competitors_only()
def game(request):
    params = get_default_dict(request)
    params['prob_list'] = models.CtfProblem.objects.all
    return render(request, 'ctf/game.html', params)


@single_http_method('GET')
class Team(DetailView):
    model = models.Team
    template_name = 'ctf/team.html'

    def get_context_data(self, **kwargs):
        context = super(Team, self).get_context_data(**kwargs)
        context.update(get_default_dict(self.request))
        return context


@single_http_method('GET')
@competitors_only()
class CurrentTeam(Team):
    def get_object(self, **kwargs):
        return self.request.user.competitor.team


# endregion


# region POSTs

# TODO(Cam): Write
# @single_http_method('POST')
# def register(request, handle, password):
#     pass


@single_http_method('POST')
@competitors_only()
def start_window(request):
    team = request.user.competitor.team
    if queries.window_active(team):
        # No point in restarting
        return redirect('ctf:game')
    queries.start_window(team)
    return redirect('ctf:game')


@single_http_method('POST')
@competitors_only()
@http_method('POST')
# XXX(Cam) - The entirety of this should probably go into some business logic file instead of here.
def submit_flag(request, problem_id):
    # TODO(Yatharth): Disable form submission if problem has already been solved (and add to Feature List)

    # Process data from the request
    flag = request.POST.get('flag', '')
    competitor = request.user.competitor
    team = competitor.team

    # Check if problem exists
    try:
        problem = queries.query_filter(models.CtfProblem, id=problem_id)
    except models.CtfProblem.DoesNotExist:
        return HttpResponseNotFound("Problem with id {} not found".format(problem_id))
    else:
        # Check if problem has already been solved
        if queries.query_filter(models.Submission, problem=problem, team=team, correct=True):
            messenger = messages.error
            message = "Your team has already solved this problem!"
            correct = None

        # Check if that flag had already been tried
        elif queries.query_filter(models.Submission, problem_id=problem_id, team=team, flag=flag):
            messenger = messages.error
            message = "You or someone on your team has already tried this flag!"
            correct = None

        else:
            # Grade
            correct, message = problem.grade(flag)
            if correct:
                messenger = messages.success

                if queries.window_active(team):
                    # Update score if correct
                    team.update_score()
                else:
                    message += '\nYour window has expired, so no points were added.'
            else:
                messenger = messages.error

        # Create submission
        queries.create_object(models.Submission, p_id=problem.id, competitor=competitor, flag=flag, correct=correct)

        # Flash message and redirect
        messenger(request, message)
        return redirect('ctf:game')

# endregion
