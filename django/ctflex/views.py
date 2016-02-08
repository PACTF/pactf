import inspect
from functools import wraps

from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import resolve
from django.core.exceptions import ValidationError
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

            SPECIAL_VIEWS = ('ctflex:inactive', 'ctflex:waiting', 'ctflex:done')
            REDIRECT_MESSAGE = "You were redirected to this page as previous page was invalid for this window."

            # TODO(Yatharth): Swap inactive and waiting?
            if not window.started():
                if view_name == 'ctflex:inactive':
                    return original_view()
                else:
                    return redirect('ctflex:inactive', window_id=window.id)
            # Window has started

            if window.ended():
                if view_name in SPECIAL_VIEWS:
                    messages.warning(request, REDIRECT_MESSAGE)
                    return redirect('ctflex:game', window_id=window.id)
                else:
                    return original_view()
            # Window has not ended

            team = request.user.competitor.team
            if not team.has_timer(window):
                if view_name in ['ctflex:waiting', 'ctflex:start_timer']:
                    return original_view()
                else:
                    return redirect('ctflex:waiting', window_id=window.id)
            # There is an active or expired timer

            if not team.timer(window).active():
                if view_name == 'ctflex:done':
                    return original_view()
                else:
                    return redirect('ctflex:done', window_id=window.id)
            # There is an active timer

            if view_name in SPECIAL_VIEWS:
                messages.warning(request, REDIRECT_MESSAGE)
                return redirect('ctflex:game', window_id=window.id)

            return original_view()

        return decorated

    return decorator


# endregion

def register(request, form=None):
    if form is None: form = RegistrationForm()
    d = get_default_dict(request)
    d['form'] = form
    return render(request, 'registration/register.html', d)

# region GETs



@single_http_method('GET')
def index(request):
    return render(request, 'ctflex/misc/index.html', get_default_dict(request))


@single_http_method('GET')
@windowed()
def inactive(request, *, window_id):
    return render(request, 'ctflex/states/waiting.html', get_window_dict(request, queries.get_window(window_id)))


@single_http_method('GET')
@windowed()
def waiting(request, *, window_id):
    return render(request, 'ctflex/states/inactive.html', get_window_dict(request, queries.get_window(window_id)))


@single_http_method('GET')
@windowed()
def done(request, *, window_id):
    return render(request, 'ctflex/states/done.html', get_window_dict(request, queries.get_window(window_id)))


@single_http_method('GET')
@competitors_only()
@windowed()
def game(request, *, window_id):
    window = queries.get_window(window_id)
    params = get_window_dict(request, window)
    params['prob_list'] = queries.viewable_problems(request.user.competitor.team, window)
    warn_historic(request, window)
    return render(request, 'ctflex/misc/game.html', params)


@single_http_method('GET')
def board(request, *, window_id):
    window = queries.get_window(window_id)
    params = get_window_dict(request, window)
    # Move to queries
    params['teams'] = queries.board(window)
    warn_historic(request, window)
    return render(request, 'ctflex/board/board_specific.html', params)

@single_http_method('GET')
def board_overall(request):
    params = get_default_dict(request)
    # Move to queries
    params['teams'] = queries.board(window=None)
    return render(request, 'ctflex/board/board_overall.html', params)


@single_http_method('GET')
class Team(DetailView):
    model = models.Team
    template_name = 'ctflex/misc/team.html'

    def get_context_data(self, **kwargs):
        # TODO: use windowed decorator somehow?
        window = queries.get_window(self.kwargs['window_id'])
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

@single_http_method('POST')
def register_user(request):
    form = RegistrationForm(request.POST)
    if not form.is_valid():
        print(form.errors)
        return register(request, form)
    # handle, pswd, email, team, team_pass = form.cleaned_data
    team, msg = queries.validate_team(form.cleaned_data['team'], form.cleaned_data['team_pass'])
    if team is None:
        form.add_error('team', msg)
        return register(request, form)
    handle = form.cleaned_data['handle']
    pswd = form.cleaned_data['pswd']
    email = form.cleaned_data['email']
    try:
        c = queries.create_competitor(handle, pswd, email, team)
        u = authenticate(username=handle, password=pswd)
        login(request, u)
        return redirect('ctflex:index')
    except ValidationError:
        form.add_error('handle', "Can't create user")
        return register(request, form)


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
def submit_flag(request, *, window_id, prob_id):

    # Process data from the request
    flag = request.POST.get('flag', '')
    competitor = request.user.competitor
    window = queries.get_window(window_id)

    # Grade
    try:
        correct, message = queries.submit_flag(prob_id, competitor, flag)
    except models.CtfProblem.DoesNotExist:
        return HttpResponseNotFound("Problem with id {} not found".format(prob_id))
    except queries.ProblemAlreadySolvedException:
        messenger = messages.error
        message = "Your team has already solved this problem!"
        correct = None
    except queries.FlagAlreadyTriedException:
        messenger = messages.error
        message = "You or someone on your team has already tried this flag!"
        correct = None
    else:
        messenger = messages.success if correct else messages.error

    # Flash message and redirect
    messenger(request, message)
    return redirect('ctflex:game', window_id=window.id)

# endregion

# region forms

class RegistrationForm(forms.Form):
    handle = forms.CharField(label='Username:', max_length=100)
    pswd = forms.CharField(label='Password:', widget=forms.PasswordInput())
    email = forms.EmailField(label='Email:')
    team = forms.CharField(label='Team:', max_length=80)
    team_pass = forms.CharField(label='Team passphrase:', max_length=30)

# endregion
