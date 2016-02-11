"""Route URLs to apps"""

from django.contrib.auth import urls as auth_urls
from django.contrib.auth import views as auth_views
from django.conf.urls import include, url
from django.contrib import admin

from ratelimit.decorators import ratelimit


urlpatterns = [
    url(r'^login/$', ratelimit(key='ip', rate='5/m')(auth_views.login)),
    url(r'^logout/$', auth_views.logout, {'next_page': 'ctflex:index'}),
    url('^', include(auth_urls)),

    url(r'^admin/', include(admin.site.urls), name='admin'),

    url(r'', include('ctflex.urls')),
    url(r'', include('pactf_web.urls')),
]
