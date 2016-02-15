"""Route URLs to apps"""

from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls), name='admin'),
    url(r'', include('ctflex.urls')),
    url(r'', include('pactf_web.urls')),
]
