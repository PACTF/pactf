"""Route URLs to apps"""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from ratelimit.decorators import ratelimit

import ctflex.views

handler404 = ctflex.views.handler_factory(404)  # page not found
handler500 = ctflex.views.handler_factory(500)  # internal server error
handler403 = ctflex.views.handler_factory(403)  # permission denied
handler402 = ctflex.views.handler_factory(401)  # bad request

admin.autodiscover()
admin.site.login = (
    ratelimit(key='ip', rate='1/s', method='POST', block=True)(
        ratelimit(key='ip', rate='10/h', method='POST', block=True)(
            admin.site.login)))

urlpatterns = [
    url(r'^{}/'.format(settings.ADMIN_URL_PATH), include(admin.site.urls), name='admin'),
    url(r'', include('ctflex.urls')),
    url(r'', include('pactf_web.urls')),
]
