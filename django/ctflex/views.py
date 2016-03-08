"""Define views"""

import inspect
import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
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
from ctflex import forms
from ctflex import models
from ctflex import queries
from ctflex import settings


# region Helper Methods

def is_competitor(user):
    return user.is_authenticated() and hasattr(user, models.Competitor.user.field.rel.name)


def default_context(request):
    """Return context needed for all CTFlex templates

    This context processor is included as the global context processor in
    `settings.py`; therefore, it should not be manually included.
    """
    return {
        'team': request.user.competitor.team if is_competitor(request.user) else None,
        'contact_email': settings.CONTACT_EMAIL,
    }


def windowed_context(window):
    """Return context needed for CTFlex templates using the window dropdown"""
    return {
        'window': window,
        'windows': queries.all_windows(),
    }


# endregion


# region Decorators

def universal_decorator(*, methodname):
    """Decorates a view decorator to decorate both function- and class-based views

    Purpose:
        If you decorate your view decorator with this decorator, your decorator
        can be written as if only applicable to a function-based view but still
        work on a class-based view

    Usage:
        Apply this decorator to a decorator of your own like so:

            @universal_decorator(methodname='<some_method>')
            def your_decorator(<arguments>):
                def decorator(view):
                    def decorated(request, *args, **kwargs):
                        <do things>
                        return view(request, *args, **kwargs)
                    return decorated
                return decorator

    Limitations:
        - Your decorator must take arguments. Make your decorator take zero
          arguments if you need to.

    Author: Yatharth
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
    """Decorate views to restrict the allowed HTTP methods"""

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
    """Decorates views to redirect non-competitor users to the login page"""
    return user_passes_test(is_competitor)


@universal_decorator(methodname='dispatch')
def anonyomous_users_only(redirect_url=settings.INVALID_STATE_REDIRECT_URL):
    """Decorates views to redirect already authenticated users away"""

    def decorator(view):
        @wraps(view)
        def decorated(request, *args, **kwargs):
            if not request.user.is_anonymous():
                messages.warning(request, "You are already logged in.")
                return HttpResponseRedirect(reverse(redirect_url))

            return view(request, *args, **kwargs)

        return decorated

    return decorator


def defaulted_window():
    """Decorates views to default their window paramater to the current window

    Purpose:
        Using this decorator, you can write your view to expect a `window_codename`
        parameter, and if this parameter is not passed in, this decorator will
        set it to the current window and then call your view.
    """

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


# endregion

# region Simple GETs

@limited_http_methods('GET')
def index(request):
    return render(request, 'ctflex/misc/index.html', {
        'windows': queries.all_windows(),
    })


@limited_http_methods('GET')
def rate_limited(request, err):
    """Render template for when the user has been rate limited

    Usage:
        This view is automatically called by the `ratelimit` module,
        so nothing more needs to be done.
    """
    return render(request, 'ctflex/misc/ratelimited.html')


# TODO(Yatharth): For viewing other teams, needs to use a slightly different template at least and be linked from scoreboard
@competitors_only()
@limited_http_methods('GET')
class Team(DetailView):
    model = models.Team
    template_name = 'ctflex/misc/team.html'

    def get_object(self, **kwargs):
        return self.request.user.competitor.team

    def get_context_data(self, **kwargs):
        context = super(Team, self).get_context_data(**kwargs)
        return context


# endregion

# region POSTs

@competitors_only()
@limited_http_methods('POST')
@never_cache
def start_timer(request):
    """Start a team’s timer and redirect to the game"""

    window = queries.get_window()
    team = request.user.competitor.team

    success = commands.start_timer(team=team, window=window)

    if not success:
        messages.error(request, "Your timer could not be started.")

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
        correct, message = commands.submit_flag(
            prob_id=prob_id, competitor=competitor, flag=flag)
    except models.CtfProblem.DoesNotExist:
        return HttpResponseNotFound()
    except commands.ProblemAlreadySolvedException:
        status = ALREADY_SOLVED_STATUS
        message = "Your team has already solved this problem!"
    except commands.FlagAlreadyTriedException:
        status = FAILURE_STATUS
        message = "Your team has already tried this flag!"
    except commands.FlagSubmissionNotAllowedException:
        status = FAILURE_STATUS
        message = "Your timer must have expired; reload the page."
    except commands.EmptyFlagException:
        status = FAILURE_STATUS
        message = "The flag was empty."
    else:
        status = SUCCESS_STATUS if correct else FAILURE_STATUS

    return JsonResponse({
        STATUS_FIELD: status,
        MESSAGE_FIELD: message
    })


# endregion

# region Complex GETs

@competitors_only()
@defaulted_window()
@limited_http_methods('GET')
@never_cache
def game(request, *, window_codename):
    """Display problems"""

    # Define countdown
    COUNTDOWN_ENDTIME_KEY = 'countdown_endtime'
    COUNTDOWN_MAX_MICROSECONDS_KEY = 'countdown_max_microseconds'

    # Process request
    team = request.user.competitor.team
    try:
        window = queries.get_window(window_codename)
    except models.Window.DoesNotExist:
        return HttpResponseNotFound()

    # Initialize context
    context = windowed_context(window)
    context['prob_list'] = queries.problem_list(team=team, window=window)
    js_context = {}

    if not window.started():
        template_name = 'ctflex/game/waiting.html'

        js_context[COUNTDOWN_ENDTIME_KEY] = window.start.isoformat()

    elif window.ended():
        template_name = 'ctflex/game/ended.html'

        current_window = queries.get_window()
        context['current_window'] = current_window

        # Check whether the current window is (in)active and
        # so whether the team could still solve problems
        context['can_compete_in_current_window'] = (
            current_window.ongoing()
            and (
                not team.has_timer(window)
                or team.has_active_timer(window)
            )
        )

    elif not team.has_timer(window):
        template_name = 'ctflex/game/inactive.html'

        js_context[COUNTDOWN_ENDTIME_KEY] = window.end.isoformat()
        js_context[COUNTDOWN_MAX_MICROSECONDS_KEY] = (
            window.personal_timer_duration.total_seconds() * 1000
        )

    elif not team.has_active_timer(window):
        template_name = 'ctflex/game/expired.html'

    else:
        template_name = 'ctflex/game/active.html'

        js_context[COUNTDOWN_ENDTIME_KEY] = team.timer(window).end.isoformat()

    context['js_context'] = json.dumps(js_context)
    return render(request, template_name, context)


@defaulted_window()
@limited_http_methods('GET')
@never_cache
def board(request, *, window_codename):
    """Displays rankings"""

    # Get window
    if window_codename == settings.OVERALL_WINDOW_CODENAME:
        window = None
    else:
        try:
            window = queries.get_window(window_codename)
        except models.Window.DoesNotExist:
            return HttpResponseNotFound()

    # Initialize context
    context = windowed_context(window)
    context['board'] = queries.board(window)
    context['overall_window_codename'] = settings.OVERALL_WINDOW_CODENAME

    # Select correct template
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
                         redirect_url=settings.TEAM_CHANGE_REDIRECT_URL):
    messages.success(request, message)
    return redirect(redirect_url)


@limited_http_methods('GET')
def password_reset_complete(request, *,
                            message="Your password was successfully set. You can log in now.",
                            redirect_url='ctflex:index'):
    messages.success(request, message)
    return redirect(redirect_url)


# endregion


# region Registration

# TODO(Yatharth): Shorten view by extracting a command
@anonyomous_users_only()
@limited_http_methods('GET', 'POST')
@sensitive_post_parameters()
@csrf_protect
@never_cache
def register(request,
             template_name='ctflex/auth/register.html',
             post_change_redirect='ctflex:game',
             extra_context=None):
    """Display registration form"""

    # Define constants

    TEAM_STATUS_NAME = 'team-status'
    TEAM_STATUS_NEW = 'new'
    TEAM_STATUS_OLD = 'old'

    class DummyException(Exception):
        pass
    # # Initialize redirect URL
    # if post_change_redirect is None:
    #     post_change_redirect = resolve_url('ctflex:game', window_codename=queries.get_window().codename)
    # else:
    #     post_change_redirect = resolve_url(post_change_redirect)

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

                    # Save form without without committing the competitor
                    # since it needs to reference the user and team
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

                        # Raise a dummy exception to let the atomic transaction
                        # manager know that shit happened so that it rolls back
                        raise DummyException()

            # Don't do anything more with the dummy exception than
            # what the atomic transaction manager would already have
            # done for us by rolling back
            except DummyException:
                pass

            # If no errors were raised, log the user in and redirect!
            else:
                auth_user = authenticate(
                    username=user_form.cleaned_data['username'],
                    password=user_form.cleaned_data['password1'],
                )
                auth_login(request, auth_user)

                messages.success(request, "You were successfully registered!")
                return HttpResponseRedirect(reverse(post_change_redirect))

    # Otherwise, create blank forms
    else:
        team_status = ''
        user_form = forms.UserCreationForm()
        competitor_form = forms.CompetitorCreationForm()
        new_team_form = forms.TeamCreationForm()
        existing_team_form = forms.TeamJoiningForm()

    # Initialize context
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

# region Misc

@limited_http_methods('GET')
def news(request):
    context = default_context(request)
    context['announcements'] = queries.all_announcements()
    if is_competitor(request.user):
        request.user.competitor.unread_announcements.clear()
    return render(request, 'ctflex/misc/news.html', context)

@limited_http_methods('GET')
def check_news(request):
    if not is_competitor(request.user):
        return JsonResponse({ 'num_unread' : 0 })
    return JsonResponse({
        'num_unread' : request.user.competitor.unread_announcements.count()
    })

# endregion
