"""Define logging-related functionality"""

import logging
from collections import OrderedDict
from functools import wraps

from ctflex.constants import IP_LOGGER_NAME, BASE_LOGGER_NAME
from ctflex import queries

logger = logging.getLogger(BASE_LOGGER_NAME + '.' + __name__)
ip_logger = logging.getLogger(IP_LOGGER_NAME + '.' + __name__)


# region Helpers

def _format_request(request, response=None):
    info = OrderedDict()

    # Request info
    info['method'] = request.method
    info['path'] = request.path[:255]
    info['is_secure'] = request.is_secure()
    info['is_ajax'] = request.is_ajax()

    # Don't log polls
    if info['path'] == '/api/unread_announcements/':
        return

    # User info
    info['ip'] = request.META.get('REMOTE_ADDR', '')
    info['referer'] = request.META.get('HTTP_REFERER', '')[:255]
    info['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:255]
    info['language'] = request.META.get('HTTP_ACCEPT_LANGUAGE', '')[:255]
    info['user'] = request.user if hasattr(request, 'user') and request.user.is_authenticated() else None
    info['competitor'] = getattr(info['user'], 'competitor', None)
    info['team'] = getattr(info['competitor'], 'team', None)

    # Redirect info
    info['status_code'] = None
    info['redirect'] = None
    if response:
        info['status_code'] = response.status_code
        if response.status_code in (301, 302):
            info['redirect'] = response['Location']

    # Stringify, trim and return
    message = str(info)[12:-1]
    return message


def _catch_errors(function):
    """Decorate loggers to never raise an exception"""

    @wraps(function)
    def decorated(*args, **kwargs):
        try:
            value = function(*args, **kwargs)
        except:
            logger.error("could not log", exc_info=True)
        else:
            return value

    return decorated


# endregion


# region Loggers

@_catch_errors
def log_request(request, response):
    message = _format_request(request, response)
    if message:
        ip_logger.info("request: {}".format(message))


@_catch_errors
def log_solve(request, solve):
    ip_logger.info("solve of {!r}: {}".format(solve.problem, _format_request(request)))


@_catch_errors
def log_timer(request, success):
    success_message = "started" if success else "failed"
    message = _format_request(request)
    ip_logger.info("timer {}: {}".format(success_message, message))


@_catch_errors
def log_login(sender, request, user, **kwargs):
    ip_logger.info("login: {}".format(_format_request(request)))


@_catch_errors
def log_logout(sender, request, user, **kwargs):
    ip_logger.info("logout: {}".format(_format_request(request)))


@_catch_errors
def log_registration(request, team, new):
    eligible = "eligible" if queries.eligible(team) else "ineligible"
    message = _format_request(request)

    if new:
        ip_logger.info("register new {} team: {}".format(eligible, message))
    else:
        ip_logger.info("join old {} team: {}".format(eligible, message))

# endregion
