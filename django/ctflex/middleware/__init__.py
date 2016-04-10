"""Define middleware"""

import logging
from collections import OrderedDict
from importlib import import_module

from ratelimit.exceptions import Ratelimited

from ctflex.middleware.utils import browsers
from ctflex import constants
from ctflex import settings
from ctflex import views

logger = logging.getLogger(constants.BASE_LOGGER_NAME + '.' + __name__)


class RatelimitMiddleware:
    """Simulate `ratelimit.middleware.RatelimitMiddleware`

    The reason this simulation has to happen is that the original middleware
    would import `import_module` from a location that doesn’t work with Django 1.9.
    """

    def process_exception(self, request, exception):
        """Copied over from `ratelimit.middleware.RatelimitMiddleware.process_exception`"""

        if not isinstance(exception, Ratelimited):
            return
        module_name, _, view_name = settings.RATELIMIT_VIEW.rpartition('.')
        module = import_module(module_name)
        view = getattr(module, view_name)
        return view(request, exception)


class IncubatingMiddleware:
    """Conditionally enabled CTFlex’s incubating mode

    Incubating mode means only bare functionality needed leading up to a
    contest is enabled.
    """

    ALLOWED_URLS = (
        'index',
        'register',
        'register_done',
        'logout',
    )

    def process_response(self, request, response):

        if not settings.INCUBATING:
            return response

        if not request.resolver_match:
            return response

        if not (request.resolver_match.namespaces
                and request.resolver_match.namespaces[0] == constants.APP_NAME):
            return response

        if request.resolver_match.url_name in self.ALLOWED_URLS:
            return response

        if (len(request.resolver_match.namespaces) >= 2
            and request.resolver_match.namespaces[1] == constants.API_NAMESPACE):
            return response

        return views.incubating(request)


class CloudflareRemoteAddrMiddleware:
    """Replace REMOTE_ADDR with Cloudflare-sent info when appropriate"""

    def process_request(self, request):
        # TODO(Yatharth): Use HTTP_X_FORWARDED_FOR if CF doesn’t work

        REMOTE_ADDR = 'REMOTE_ADDR'
        HTTP_CF_CONNECTING_IP = 'HTTP_CF_CONNECTING_IP'
        EMPTY_IPS = ('', "b''")

        logger.debug("cloudflare: IP is {}".format(
            request.META.get(REMOTE_ADDR, '')))
        if request.META.get(REMOTE_ADDR, '') in EMPTY_IPS:
            logger.debug("cloudflare: changing IP from {} to {}".format(
                request.META.get(REMOTE_ADDR, ''),
                request.META.get(HTTP_CF_CONNECTING_IP, '')))
            request.META[REMOTE_ADDR] = request.META.get(HTTP_CF_CONNECTING_IP, '')


class RequestLoggingMiddleware:
    logger = logging.getLogger(constants.IP_LOGGER_NAME)

    def process_response(self, request, response):

        info = OrderedDict()

        # Request info
        info['method'] = request.method
        info['path'] = request.path[:255]
        info['is_secure'] = request.is_secure()
        info['is_ajax'] = request.is_ajax()

        if info['path'] == '/api/unread_announcements/':
            return response

        # User info
        info['ip'] = request.META.get('REMOTE_ADDR', '')
        info['referer'] = request.META.get('HTTP_REFERER', '')[:255]
        info['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:255]
        info['language'] = request.META.get('HTTP_ACCEPT_LANGUAGE', '')[:255]
        info['user'] = request.user if getattr(request, 'user', False) and request.user.is_authenticated() else None

        # Redirect info
        info['status_code'] = None
        info['redirect'] = None
        if response:
            info['status_code'] = response.status_code
            if response.status_code in (301, 302):
                info['redirect'] = response['Location']

        message = str(info)[13:-2]
        self.logger.info(message)

        return response
