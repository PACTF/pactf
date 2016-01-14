import inspect
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
    result['is_active_window'] = models.Window.active()
    result['can_view_problems'] = models.Window.active() and team and team.can_view_problems()
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

            @wraps(old_decorator)
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
        @wraps(view)
        def decorated(request, *args, **kwargs):
            if request.method != method:
                return error
            return view(request, *args, **kwargs)

        return decorated

    return decorator


@universal_decorator(methodname='dispatch')
def competitors_only():
    return user_passes_test(is_competitor)


@universal_decorator(methodname='get')
def active_window_only():
    def decorator(view):
        @wraps(view)
        def decorated(request, *args, **kwargs):
            if not models.Window.active():
                messages.warning(request, "No window is currently active.")
                return redirect('ctf:index')

            return view(request, *args, **kwargs)

        return decorated

    return decorator


# endregion


# region GETs

@single_http_method('GET')
def index(request):
    return render(request, 'ctf/index.html', get_default_dict(request))


@single_http_method('GET')
@competitors_only()
@active_window_only()
def game(request):
    params = get_default_dict(request)
    params['prob_list'] = queries.viewable_problems(request.user.competitor.team)
    return render(request, 'ctf/game.html', params)


@single_http_method('GET')
def board(request):
    params = get_default_dict(request)
    params['teams'] = enumerate(models.Team.objects.order_by('-score'))
    return render(request, 'ctf/board.html', params)

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
@active_window_only()
def start_window(request):
    team = request.user.competitor.team

    if team.has_timer():
        if team.has_active_timer():
            messages.warning("Your timer has already started.")
            return redirect('ctf:game')
        else:
            messages.error("Your timer for this window has expired.")
            return redirect('ctf:index')

    team.start_timer()
    return redirect('ctf:game')


@single_http_method('POST')
@competitors_only()
@active_window_only()
# XXX(Cam): Move all of this elsewhere
def submit_flag(request, problem_id):
    # Process data from the request
    flag = request.POST.get('flag', '')
    competitor = request.user.competitor
    team = competitor.team

    if not team.has_active_timer():
        if team.has_timer():
            message = "Your timer for this window has already expired."
        else:
            message = "Start your timer before submitting flags."
        messages.error(request, message)

        return redirect('ctf:index')

    # Check if problem exists
    try:
        problem = queries.query_get(models.CtfProblem, id=problem_id)
    except models.CtfProblem.DoesNotExist:
        return HttpResponseNotFound("Problem with id {} not found".format(problem_id))

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

    # Grade
    else:
        correct, message = problem.grade(flag, team)

        if correct:
            messenger = messages.success
            queries.update_score(team, problem)
        else:
            messenger = messages.error

    # Create submission
    queries.create_object(models.Submission, p_id=problem.id, problem=problem, team=team, competitor=competitor, flag=flag, correct=correct)

    # Flash message and redirect
    messenger(request, message)
    return redirect('ctf:game')

# endregion
