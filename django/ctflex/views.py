import inspect
from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import resolve
from django.http.response import HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.conf import settings

from ctflex import models
from ctflex import queries


# region Helper Methods

def is_competitor(user):
    return user.is_authenticated() and hasattr(user, models.Competitor.user.field.rel.name)


def get_default_dict(request):
    params = {}
    params['production'] = not settings.DEBUG
    team = request.user.competitor.team if is_competitor(request.user) else None
    params['team'] = team
    return params


def get_window_dict(request, window):
    params = get_default_dict(request)
    params['window'] = window
    params['is_active_window'] = window.start
    return params


def warn_historic(request, window):
    """Flash info if in a historic state"""
    if window.ended():
        messages.info(request,
                      "This window has ended. You may still solve problems, but the scoreboard has been frozen.")


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


def windowed():
    def decorator(view):
        @wraps(view)
        def decorated(request, *args, window_id, **kwargs):
            window = queries.get_window(window_id)
            view_name = resolve(request.path_info).view_name
            original_view = lambda: view(request, *args, window_id=window_id, **kwargs)

            print(window.start, timezone.now(), window.start <= timezone.now(), window.started())
            if not window.started():
                if view_name == 'ctflex:inactive':
                    return original_view()
                else:
                    return redirect('ctflex:inactive', window_id=window.id)
            # Window has started

            if window.ended():
                return original_view()
            # Window has not ended

            team = request.user.competitor.team
            if not team.has_timer(window):
                if view_name in ['ctflex:waiting', 'ctflex:start_timer']:
                    return original_view()
                else:
                    return redirect('ctflex:waiting', window_id=window.id)
            # There is/was a timer

            if not team.timer(window).active():
                if view_name == 'ctflex:done':
                    return original_view()
                else:
                    return redirect('ctflex:done', window_id=window.id)
            # There is a timer

            return original_view()

        return decorated

    return decorator


# endregion


# region GETs


@single_http_method('GET')
def index(request):
    return render(request, 'ctflex/index.html', get_default_dict(request))


@single_http_method('GET')
@windowed()
def inactive(request, *, window_id):
    return render(request, 'ctflex/waiting.html', get_window_dict(request, queries.get_window(window_id)))


@single_http_method('GET')
@windowed()
def waiting(request, *, window_id):
    return render(request, 'ctflex/inactive.html', get_window_dict(request, queries.get_window(window_id)))


@single_http_method('GET')
@windowed()
def done(request, *, window_id):
    return render(request, 'ctflex/done.html', get_window_dict(request, queries.get_window(window_id)))


@single_http_method('GET')
@competitors_only()
@windowed()
def game(request, *, window_id):
    window = queries.get_window(window_id)
    params = get_window_dict(request, window)
    params['prob_list'] = queries.viewable_problems(request.user.competitor.team, window)
    warn_historic(request, window)
    return render(request, 'ctflex/game.html', params)


@single_http_method('GET')
@windowed()
def board(request, *, window_id):
    window = queries.get_window(window_id)
    params = get_window_dict(request, window)
    params['teams'] = enumerate(sorted(models.Team.objects.all(), key=lambda team: team.score(window), reverse=True))
    warn_historic(request, window)
    return render(request, 'ctflex/board.html', params)


@single_http_method('GET')
class Team(DetailView):
    model = models.Team
    template_name = 'ctflex/team.html'

    def get_context_data(self, *, window_id, **kwargs):
        # TODO: use windowed decorator somehow?
        window = queries.get_window(window_id)
        context = super(Team, self).get_context_data(**kwargs)
        context.update(get_window_dict(self.request, window))
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
# def register_competitor(handle, pswd, team=None):
#    pass


@single_http_method('POST')
@competitors_only()
@windowed()
def start_timer(request, *, window_id):
    window = queries.get_window(window_id)
    team = request.user.competitor.team

    if team.has_timer(window):
        if team.has_active_timer(window):
            messages.warning(request, "Your timer has already started.")
            return redirect('ctflex:game', window_id=window.id)
        else:
            messages.error(request, "Your timer for this window has expired.")
            return redirect('ctflex:index')

    team.start_timer(window)
    return redirect('ctflex:game', window_id=window.id)


@single_http_method('POST')
@competitors_only()
@windowed()
# XXX(Cam): Move all of this elsewhere
def submit_flag(request, *, window_id, prob_id):
    # Process data from the request
    flag = request.POST.get('flag', '')
    competitor = request.user.competitor
    team = competitor.team
    window = queries.get_window(window_id)

    if not team.has_active_timer():
        if team.has_timer():
            message = "Your timer for this window has already expired."
        else:
            message = "Start your timer before submitting flags."
        messages.error(request, message)

        return redirect('ctflex:index')

    # Check if problem exists
    try:
        problem = queries.query_get(models.CtfProblem, id=prob_id)
    except models.CtfProblem.DoesNotExist:
        return HttpResponseNotFound("Problem with id {} not found".format(prob_id))

    # Check if problem has already been solved
    if queries.query_filter(models.Submission, problem=problem, team=team, correct=True):
        messenger = messages.error
        message = "Your team has already solved this problem!"
        correct = None

    # Check if that flag had already been tried
    elif queries.query_filter(models.Submission, problem_id=prob_id, team=team, flag=flag):
        messenger = messages.error
        message = "You or someone on your team has already tried this flag!"
        correct = None

    # Grade
    else:
        correct, message = problem.grade(flag, team)

        if correct:
            messenger = messages.success
            queries.update_score(competitor=competitor, problem=problem, flag=flag)
        else:
            messenger = messages.error

    # Create submission
    queries.create_object(models.Submission, p_id=problem.id, problem=problem, team=team, competitor=competitor,
                          flag=flag, correct=correct)

    # Flash message and redirect
    messenger(request, message)
    return redirect('ctflex:game', window_id=window.id)

# endregion
