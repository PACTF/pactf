import inspect
from copy import copy
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve, reverse
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.http.response import HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import render, redirect, resolve_url
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import DetailView
from ratelimit.utils import is_ratelimited

from ctflex import commands
from ctflex import constants
from ctflex import forms
from ctflex import models
from ctflex import queries
from ctflex.constants import TEAM_STATUS_NAME, TEAM_STATUS_NEW, TEAM_STATUS_OLD


# region Helper Methods

def is_competitor(user):
    return user.is_authenticated() and hasattr(user, models.Competitor.user.field.rel.name)


def default_context(request):
    """Return default CTFlex context

    This context processor is included as the global context processor in settings.py; therefore, it should not be manually included.
    """
    params = {}
    params['production'] = not settings.DEBUG
    params['team'] = request.user.competitor.team if is_competitor(request.user) else None

    params['window'] = queries.get_window(request.resolver_match.kwargs.get('window_id', ''))
    params['other_windows'] = models.Window.objects.other(params['window'])
    return params


def warn_historic(request, window):
    """Flash info if in a historic state"""
    if window.ended():
        messages.info(request,
                      "This window has ended. You may still solve problems, but the scoreboard has been frozen.")


# endregion


# region Decorators

def universal_decorator(*, methodname):
    """Makes a decorator factory able to decorate both a function and a certain method of a class

    Usage: Apply this decorator to a decorator of your own like so:

        @universal_decorator(methodname='<some_method>')
        def your_decorator(<arguments>):
            def decorator(view):
                def decorated(request, *args, **kwargs):
                    <do things>
                    return view(request, *args, **kwargs)
                return decorated
            return decorator

    Drawbacks:
    - This meta-decorator factory does NOT work on non-factory decorators (decorators that do not take arguments). Make a decorator factory that takes no arguments if you must.

    For help, contact Yatharth.
    """

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
def limited_http_methods(*methods):
    """Decorates views to check for HTTP method"""

    assert set(methods).issubset({'GET', 'POST', 'PUT', 'DELETE'}), ValueError(
        "Not all methods recognized: {}".format(methods))
    # TODO(Yatharth): Show custom page per http://stackoverflow.com/questions/4614294
    error = HttpResponseNotAllowed('Only the following HTTP methods are allowed here: {}'.format(methods))

    def decorator(view):
        @wraps(view)
        def decorated(request, *args, **kwargs):
            if request.method not in methods:
                return error
            return view(request, *args, **kwargs)

        return decorated

    return decorator


@universal_decorator(methodname='dispatch')
def competitors_only():
    return user_passes_test(is_competitor)


@universal_decorator(methodname='dispatch')
def anonyomous_users_only():
    """Redirect already authenticated users away"""

    def decorator(view):
        @wraps(view)
        def decorated(request, *args, **kwargs):
            if not request.user.is_anonymous():
                messages.warning(request, "You are already logged in.")
                return HttpResponseRedirect(reverse(constants.INVALID_STATE_REDIRECT_URL))

            return view(request, *args, **kwargs)

        return decorated

    return decorator

@universal_decorator(methodname='dispatch')
def redirected_from_no_window(*, takes_window_param=False):
    """If no window argument is present, redirect to current window"""

    def decorator(view):
        @wraps(view)
        def decorated(request, *args, **kwargs):
            if 'window_id' not in kwargs:
                kwargs['window_id'] = queries.get_window().id
                return redirect(reverse(request.resolver_match.view_name, args=args, kwargs=kwargs))
            else:
                if not takes_window_param:
                    del kwargs['window_id']
                return view(request, *args, **kwargs)

        return decorated

    return decorator


def windowed():
    """Redirects views around based on Contest Window and Personal Timer states

    This decorator wraps views with competitors_only() and redirected_from_no_window() too, so do not decorate a view with either of them if you are already using windowed() since doing so would be redundant.
    """

    def decorator(view):

        @wraps(view)
        @competitors_only()
        @redirected_from_no_window(takes_window_param=True)
        def decorated(request, *args, window_id, **kwargs):

            window = queries.get_window(window_id)
            view_name = resolve(request.path_info).view_name
            original_view = lambda: view(request, *args, window_id=window_id, **kwargs)

            STATE_VIEWS = ('ctflex:waiting', 'ctflex:inactive', 'ctflex:done')
            REDIRECT_MESSAGE = "You were redirected to this page as previous page was invalid for this window."

            if not window.started():
                if view_name == 'ctflex:waiting':
                    return original_view()
                else:
                    return redirect('ctflex:waiting', window_id=window.id)
            # Window has started

            if window.ended():
                if view_name in STATE_VIEWS:
                    messages.warning(request, REDIRECT_MESSAGE)
                    return redirect('ctflex:game', window_id=window.id)
                else:
                    return original_view()
            # Window has not ended

            team = request.user.competitor.team
            if not team.has_timer(window):
                if view_name in ['ctflex:inactive', 'ctflex:start_timer']:
                    return original_view()
                else:
                    return redirect('ctflex:inactive', window_id=window.id)
            # There is an active or expired timer

            if not team.timer(window).active():
                if view_name == 'ctflex:done':
                    return original_view()
                else:
                    return redirect('ctflex:done', window_id=window.id)
            # There is an active timer

            if view_name in STATE_VIEWS:
                messages.warning(request, REDIRECT_MESSAGE)
                return redirect('ctflex:game', window_id=window.id)

            return original_view()

        return decorated

    return decorator


# endregion

# region State Views

@limited_http_methods('GET')
@windowed()
def inactive(request, *, window_id):
    return render(request, 'ctflex/states/inactive.html', request)


@limited_http_methods('GET')
@windowed()
def waiting(request, *, window_id):
    return render(request, 'ctflex/states/waiting.html', request)


@limited_http_methods('GET')
@windowed()
def done(request, *, window_id):
    return render(request, 'ctflex/states/done.html', request)


@limited_http_methods('POST')
@windowed()
def start_timer(request, *, window_id):
    window = queries.get_window(window_id)
    team = request.user.competitor.team

    success, msgs = commands.start_timer(team=team, window=window)

    if not success:
        for msg in msgs:
            messages.error(request, msg)

    return redirect('ctflex:game', window_id=window.id)


# endregion


# region Misc Views


@limited_http_methods('GET')
def index(request, *, window_id=None):
    """Index

    It takes window_id since all other views take it and didn't want to make exception for index page
    but it resets you to current window because:
    - the index page should return a user back to the 'home'
    - this isn't as good of a reason, but it's just hard to think of how to get passed the window info without
    getting it via a URL but then having a URL like  /window1/ looks like it is just for windo1 and not a general index page
    """
    return render(request, 'ctflex/misc/index.html')


@limited_http_methods('GET')
@redirected_from_no_window()
def rate_limited(request, err):
    return render(request, 'ctflex/misc/ratelimited.html')


# endregion

# region CTF Views

@limited_http_methods('GET')
@windowed()
def game(request, *, window_id):
    window = queries.get_window(window_id)

    params = {}
    params['prob_list'] = queries.viewable_problems(request.user.competitor.team, window)

    warn_historic(request, window)

    return render(request, 'ctflex/misc/game.html', params)


@limited_http_methods('GET')
@never_cache
def board(request, *, window_id):
    window = queries.get_window(window_id)

    if not window.started():
        return redirect('ctflex:waiting', window_id=window.id)

    params = {}
    params['teams'] = queries.board(window)

    warn_historic(request, window)

    return render(request, 'ctflex/board/board_specific.html', params)


@limited_http_methods('GET')
@redirected_from_no_window()
@never_cache
def board_overall(request):
    params = {}
    params['teams'] = queries.board()

    return render(request, 'ctflex/board/board_overall.html', params)


@limited_http_methods('POST')
@windowed()
def submit_flag(request, *, window_id, prob_id):
    # Handle rate-limiting
    if is_ratelimited(request, fn=submit_flag, key=queries.get_team, rate='1/s', increment=True):
        # FIXME(Yatharth): Return JSON
        return rate_limited(request, None)

    # Process data from the request
    flag = request.POST.get('flag', '')
    competitor = request.user.competitor
    window = queries.get_window(window_id)

    # Grade
    try:
        correct, message = queries.submit_flag(prob_id, competitor, flag)
    except models.CtfProblem.DoesNotExist:
        return HttpResponseNotFound("Problem with id {} not found".format(prob_id))
    # XXX(Yatharth): Change to 'status' and have a blanket except as "internal server error" and add "could not communicate" error if can't parse on client side
    except queries.ProblemAlreadySolvedException:
        correct = False
        message = "Your team has already solved this problem!"
    except queries.FlagAlreadyTriedException:
        correct = False
        message = "You or someone on your team has already tried this flag!"
    return JsonResponse({'correct': correct, 'msg': message})


# endregion

# region Team Views

# XXX(Yatharth): Needs to use a slightly different template at least
# XXX(Yatharth): Link to from scoreboard
@limited_http_methods('GET')
@redirected_from_no_window()
class Team(DetailView):
    model = models.Team
    template_name = 'ctflex/misc/team.html'

    def get_context_data(self, **kwargs):
        context = super(Team, self).get_context_data(**kwargs)
        return context


@limited_http_methods('GET')
@competitors_only()
@redirected_from_no_window()
class CurrentTeam(Team):
    def get_object(self, **kwargs):
        return self.request.user.competitor.team


# endregion


# region Auth Views

@limited_http_methods('GET')
def logout_done(request, *,
                message="You have been logged out.",
                redirect_url='ctflex:index'):
    messages.success(request, message)
    return redirect(redirect_url)


@limited_http_methods('GET')
def password_change_done(request, *,
                         message="Your password was successfully changed.",
                         redirect_url=constants.TEAM_CHANGE_REDIRECT_URL):
    messages.success(request, message)
    return redirect(redirect_url)


@limited_http_methods('GET')
def password_reset_complete(request):
    messages.success(request, "Your password was successfully set. You can log in now.")
    return redirect('ctflex:login')


class DummyAtomicException(Exception):
    pass


@limited_http_methods('GET', 'POST')
@anonyomous_users_only()
@sensitive_post_parameters()
@csrf_protect
@never_cache
def register(request,
             template_name='ctflex/auth/register.html',
             post_change_redirect=None,
             extra_context=None):
    # Initialize redirect URL
    if post_change_redirect is None:
        post_change_redirect = resolve_url('ctflex:game', window_id=queries.get_window().id)
    else:
        post_change_redirect = resolve_url(post_change_redirect)

    # If POST, process submitted data
    if request.method == 'POST':

        # Process POST data

        user_form = forms.UserCreationForm(data=request.POST)
        competitor_form = forms.CompetitorCreationForm(data=request.POST)

        team_status = request.POST.get(TEAM_STATUS_NAME, '')
        if team_status == TEAM_STATUS_OLD:
            existing_team_form = forms.TeamJoiningForm(data=request.POST)
            new_team_form = forms.TeamCreationForm()
            active_team_form = existing_team_form
        else:
            team_status = TEAM_STATUS_NEW
            new_team_form = forms.TeamCreationForm(data=request.POST)
            existing_team_form = forms.TeamJoiningForm()
            active_team_form = new_team_form

        # If valid, begin a transaction
        if user_form.is_valid() and active_team_form.is_valid() and competitor_form.is_valid():
            try:
                with transaction.atomic():

                    # Save form without without committing the competitor since it needs to reference the others
                    user = user_form.save()
                    team = active_team_form.save()
                    competitor = competitor_form.save(commit=False)

                    # Try saving the user now
                    competitor.user = user
                    competitor.team = team
                    try:
                        competitor.save()

                    # If there were errors, flash them
                    except ValidationError as err:
                        for msg in err.messages:
                            messages.error(request, msg)

                        # Let the atomic transaction manager know that shit happened so it rolls back
                        raise DummyAtomicException()

            # Don't do anything more with the dummy exception than
            # what the atomic transaction manager would have already done for us
            except DummyAtomicException:
                pass

            # Log in the user and redirect!
            else:
                auth_user = authenticate(
                    username=user_form.cleaned_data['username'],
                    password=user_form.cleaned_data['password1'],
                )
                auth_login(request, auth_user)
                messages.success(request, "You were successfully registered!")
                return HttpResponseRedirect(post_change_redirect)

    # Otherwise, create blank forms
    else:
        team_status = ''
        user_form = forms.UserCreationForm()
        competitor_form = forms.CompetitorCreationForm()
        new_team_form = forms.TeamCreationForm()
        existing_team_form = forms.TeamJoiningForm()

    # Configure context and render
    context = {
        'team_status': team_status,
        'user_form': user_form,
        'competitor_form': competitor_form,
        'new_team_form': new_team_form,
        'existing_team_form': existing_team_form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return render(request, template_name, context)

# endregion
