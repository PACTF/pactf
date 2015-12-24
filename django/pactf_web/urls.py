"""URL Config
"""

from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = (
    url(r'^admin/', include(admin.site.urls), name='admin'),
    url(r'', include('pactf_framework.urls')),
)
