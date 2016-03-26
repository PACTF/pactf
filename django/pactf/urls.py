"""Route URLs to apps"""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^{}/'.format(settings.ADMIN_URL_PATH), include(admin.site.urls), name='admin'),
    url(r'', include('ctflex.urls')),
    url(r'', include('pactf_web.urls')),
]
