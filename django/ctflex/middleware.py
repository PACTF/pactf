"""Define middleware"""

from importlib import import_module

from django.conf import settings

from ratelimit.exceptions import Ratelimited


class RatelimitMiddleware(object):
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
