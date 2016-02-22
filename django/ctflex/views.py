import inspect
from functools import wraps

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import resolve, reverse
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.http.response import HttpResponse, HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.conf import settings

from ratelimit.decorators import ratelimit
from ratelimit.utils import is_ratelimited

from ctflex import models
from ctflex import queries
from ctflex import commands
from ctflex import forms
from ctflex import constants


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
    params['window'] = queries.get_window()
    params['other_windows'] = models.Window.objects.other(params['window'])
    return params


def windowed_context(request, window):
    """Return context for windowed URLs"""
    params = {}
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

def universal_decorator(*, methodname):
    """Makes a decorator factory able to decorate both a function and a certain method of a class

    This meta-decorator factory does NOT work on non-factory decorators (decorators that do not take arguments). Make a decorator factory that takes no arguments if you must.

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
    """Redirects views around based on Contest Window and Personal Timer states

    This decorator wraps views with competitors_only() too, so do not decorate a view with both windowed() and competitors_only() because that would be redundant.
    """

    def decorator(view):

        @wraps(view)
        @competitors_only()
        def decorated(request, *args, window_id, **kwargs):

            window = queries.get_window(window_id)
            view_name = resolve(request.path_info).view_name
            original_view = lambda: view(request, *args, window_id=window_id, **kwargs)

            STATE_VIEWS = ('ctflex:waiting', 'ctflex:inactive', 'ctflex:done')
            REDIRECT_MESSAGE = "You were redirected to this page as previous page was invalid for this window."

            # TODO(Yatharth): Swap inactive and waiting?
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

@single_http_method('GET')
@windowed()
def inactive(request, *, window_id):
    return render(request, 'ctflex/states/inactive.html', windowed_context(request, queries.get_window(window_id)))


@single_http_method('GET')
@windowed()
def waiting(request, *, window_id):
    return render(request, 'ctflex/states/waiting.html', windowed_context(request, queries.get_window(window_id)))


@single_http_method('GET')
@windowed()
def done(request, *, window_id):
    return render(request, 'ctflex/states/done.html', windowed_context(request, queries.get_window(window_id)))


@single_http_method('POST')
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


@single_http_method('GET')
def index(request):
    return render(request, 'ctflex/misc/index.html')


@single_http_method('GET')
def rate_limited(request, err):
    return render(request, 'ctflex/misc/ratelimited.html')


# endregion

# region CTF Views

@single_http_method('GET')
@windowed()
def game(request, *, window_id):
    window = queries.get_window(window_id)

    params = windowed_context(request, window)
    params['prob_list'] = queries.viewable_problems(request.user.competitor.team, window)

    warn_historic(request, window)

    return render(request, 'ctflex/misc/game.html', params)


@single_http_method('GET')
@never_cache
def board(request, *, window_id):
    window = queries.get_window(window_id)

    params = windowed_context(request, window)
    params['teams'] = queries.board(window)

    warn_historic(request, window)

    return render(request, 'ctflex/board/board_specific.html', params)


@single_http_method('GET')
@never_cache
def board_overall(request):
    params = {}
    params['teams'] = queries.board()

    return render(request, 'ctflex/board/board_overall.html', params)


@single_http_method('POST')
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
@single_http_method('GET')
class Team(DetailView):
    model = models.Team
    template_name = 'ctflex/misc/team.html'

    def get_context_data(self, **kwargs):
        # TODO: use windowed decorator somehow?
        window = queries.get_window(self.kwargs['window_id'])
        context = super(Team, self).get_context_data(**kwargs)
        context.update(windowed_context(self.request, window))
        return context


@single_http_method('GET')
@competitors_only()
class CurrentTeam(Team):
    def get_object(self, **kwargs):
        return self.request.user.competitor.team


# endregion


# region Auth Views

@single_http_method('GET')
def logout_done(request, *,
                message="You have been logged out.",
                redirect_url='ctflex:index'):
    messages.success(request, message)
    return redirect(redirect_url)


@single_http_method('GET')
def password_change_done(request, *,
                         message="Your password was successfully changed.",
                         redirect_url=constants.TEAM_CHANGE_REDIRECT_URL):
    messages.success(request, message)
    return redirect(redirect_url)


@single_http_method('GET')
def password_reset_complete(request):
    messages.success(request, "Your password was successfully set. You can log in now.")
    return redirect('ctflex:login')


@sensitive_post_parameters()
@csrf_protect
@never_cache
def register(request, form_class=forms.CompetitorForm):
    return render(request, 'ctflex/auth/register.html', {
        'form': form_class()
    })


@single_http_method('POST')
@sensitive_post_parameters()
@ratelimit(key='ip', rate='5/m')
def register_user(request):
    form = forms.RegistrationForm(request.POST)
    if not form.is_valid():
        return register(request, form)
        # return JsonResponse({'errors': [[k, form.errors[k]] for k in form.errors]})
    # handle, pswd, email, team, team_pass = form.cleaned_data
    team, msg = queries.validate_team(form.cleaned_data['team'], form.cleaned_data['team_pass'])
    if team is None:
        form.add_error('team', msg)
        return register(request, form)
    handle = form.cleaned_data['handle']
    pswd = form.cleaned_data['pswd']
    email = form.cleaned_data['email']
    state = form.cleaned_data['state']
    try:
        c = queries.create_competitor(handle, pswd, email, team, state)
        u = authenticate(username=handle, password=pswd)
        login(request, u)
        # XXX(Yatharth): Ditch this
        #     return redirect('ctflex:index')
        # except ValidationError:
        #     form.add_error('handle', "Can't create user")
        #     # return register(request, form)
        #     return HttpResponseNotAllowed("POST")
        return JsonResponse({'redirect': reverse('ctflex:index')})
    except ValidationError as e:
        form.add_error('handle', str(e))
        return JsonResponse({'errors': [[k, form.errors[k]] for k in form.errors]})

# endregion
