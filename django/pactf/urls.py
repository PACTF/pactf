"""Route URLs to apps"""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from ratelimit.decorators import ratelimit

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
