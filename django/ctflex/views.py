import json
import inspect
from functools import wraps

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
from ctflex import settings
from ctflex.constants import TEAM_STATUS_NAME, TEAM_STATUS_NEW, TEAM_STATUS_OLD, WINDOW_SESSION_KEY


# TODO: Reorder decorators

# region Helper Methods

def is_competitor(user):
    return user.is_authenticated() and hasattr(user, models.Competitor.user.field.rel.name)


def default_context(request):
    """Return default CTFlex context

    This context processor is included as the global context processor in settings.py; therefore, it should not be manually included.
    """
    context = {}
    context['team'] = request.user.competitor.team if is_competitor(request.user) else None
    context['contact_email'] = settings.CONTACT_EMAIL
    return context


def windowed_context(window):
    return {
        'window': window,
        'windows': models.Window.objects.order_by('start').all,
    }


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


def defaulted_window():
    def decorator(view):
        @wraps(view)
        def decorated(request, *args, window_codename=None, **kwargs):
            if window_codename is None:
                view_name = request.resolver_match.view_name
                kwargs['window_codename'] = queries.get_window().codename
                return HttpResponseRedirect(reverse(view_name, args=args, kwargs=kwargs))

            return view(request, *args, window_codename=window_codename, **kwargs)

        return decorated

    return decorator


# region Misc Views


@limited_http_methods('GET')
def index(request):
    return render(request, 'ctflex/misc/index.html')


# @limited_http_methods('GET')
# def rate_limited(request, err):
#     return render(request, 'ctflex/misc/ratelimited.html')


@competitors_only()
@limited_http_methods('POST')
@never_cache
def start_timer(request):
    window = queries.get_window()
    team = request.user.competitor.team

    success = commands.start_timer(team=team, window=window)

    if not success:
        messages.error(request, "Your timer could not be started.")
        return redirect(reverse('ctflex:game'))

    return redirect(reverse('ctflex:game'))


@competitors_only()
@limited_http_methods('POST')
@never_cache
def submit_flag(request, *, prob_id):
    """Grade a flag submission and return a JSON response"""

    # Define constants
    STATUS_FIELD = 'status'
    MESSAGE_FIELD = 'message'
    SUCCESS_STATUS = 0
    FAILURE_STATUS = 1
    ALREADY_SOLVED_STATUS = 2

    # Rate-limit
    if is_ratelimited(request, fn=submit_flag,
                      key=queries.competitor_key, rate='2/s', increment=True):
        return JsonResponse({
            STATUS_FIELD: FAILURE_STATUS,
            MESSAGE_FIELD: "You are submitting flags too fast. Slow down!"
        })

    # Process data from the request
    flag = request.POST.get('flag', '')
    competitor = request.user.competitor

    # Grade, catching errors
    try:
        correct, message = commands.submit_flag(prob_id=prob_id, competitor=competitor, flag=flag)
    except models.CtfProblem.DoesNotExist:
        return HttpResponseNotFound("Problem with id {} not found".format(prob_id))
    except commands.ProblemAlreadySolvedException:
        status = ALREADY_SOLVED_STATUS
        message = "Your team has already solved this problem!"
    except commands.FlagAlreadyTriedException:
        status = FAILURE_STATUS
        message = "Your team has already tried this flag!"
    except commands.FlagSubmissionNotAllowException:
        status = FAILURE_STATUS
        message = "Your timer must have expired; reload the page."
    except commands.EmptyFlagException:
        status = FAILURE_STATUS
        message = "The flag was empty."
    else:
        status = SUCCESS_STATUS if correct else FAILURE_STATUS

    return JsonResponse({STATUS_FIELD: status, MESSAGE_FIELD: message})


# endregion

# region Game

@competitors_only()
@defaulted_window()
@limited_http_methods('GET')
@never_cache
def game(request, *, window_codename):
    COUNTDOWN_ENDTIME_KEY = 'countdown_endtime'
    COUNTDOWN_MAX_MICROSECONDS_KEY = 'countdown_max_microseconds'

    try:
        window = queries.get_window(window_codename)
    except models.Window.DoesNotExist:
        return HttpResponseNotFound()

    team = request.user.competitor.team
    problems = queries.viewable_problems(team=team, window=window)

    context = windowed_context(window)
    context['prob_list'] = problems
    js_context = {}

    if not window.started():
        template_name = 'ctflex/game/waiting.html'

        js_context[COUNTDOWN_ENDTIME_KEY] = window.start.isoformat()

    elif window.ended():
        template_name = 'ctflex/game/ended.html'

        # Check whether current window is inactive or active
        current_window = queries.get_window()
        context['current_window'] = current_window
        can_compete_in_current_window = current_window.started() and not current_window.ended() and (
            not team.has_timer(window) or team.has_active_timer(window))
        context['can_compete_in_current_window'] = can_compete_in_current_window

    elif not team.has_timer(window):
        template_name = 'ctflex/game/inactive.html'

        js_context[COUNTDOWN_ENDTIME_KEY] = window.end.isoformat()
        js_context[COUNTDOWN_MAX_MICROSECONDS_KEY] = window.personal_timer_duration.total_seconds() * 1000

    elif not team.has_active_timer(window):
        template_name = 'ctflex/game/expired.html'

    else:
        template_name = 'ctflex/game/active.html'

        js_context[COUNTDOWN_ENDTIME_KEY] = team.timer(window).end.isoformat()

    context['js_context'] = json.dumps(js_context)
    return render(request, template_name, context)


# endregion

# region Board


@limited_http_methods('GET')
@defaulted_window()
@never_cache
def board(request, *, window_codename):
    # Get window
    if window_codename == constants.OVERALL_WINDOW_NAME:
        window = None
    else:
        try:
            window = queries.get_window(window_codename)
        except models.Window.DoesNotExist:
            return HttpResponseNotFound()

    context = windowed_context(window)
    context['board'] = queries.board(window)
    context['overall_window_codename'] = constants.OVERALL_WINDOW_NAME

    if window is None:
        template_name = 'ctflex/board/overall.html'
    elif not window.started():
        template_name = 'ctflex/board/waiting.html'
    elif window.ended():
        template_name = 'ctflex/board/ended.html'
    else:
        template_name = 'ctflex/board/current.html'

    return render(request, template_name, context)


# endregion

# region Team

# TODO(Yatharth): For viewing other teams, needs to use a slightly different template at least and be linked from scoreboard
@limited_http_methods('GET')
@competitors_only()
class Team(DetailView):
    model = models.Team
    template_name = 'ctflex/misc/team.html'

    def get_object(self, **kwargs):
        return self.request.user.competitor.team

    def get_context_data(self, **kwargs):
        context = super(Team, self).get_context_data(**kwargs)
        return context


# endregion


# region Auth

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


@never_cache
@sensitive_post_parameters()
@csrf_protect
@anonyomous_users_only()
@limited_http_methods('GET', 'POST')
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

        # XXX: Create command

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
