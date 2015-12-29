"""URL Config
"""

from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    # TODO(Yatharth): Write custom templates (then move these rules to ctf/urls.py)
    url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': 'ctf:index'}),
    url('^', include('django.contrib.auth.urls')),

    url(r'^admin/', include(admin.site.urls), name='admin'),
    url(r'', include('ctf.urls')),
]

