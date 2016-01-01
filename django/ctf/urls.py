from django.conf.urls import url

from ctf.constants import UUID_REGEX
from ctf import views


app_name = 'ctf'

urlpatterns = [
    url('^$', views.index, name='index'),
    url(r'^game$', views.game, name='game'),
    url(r'^team$', views.CurrentTeam.as_view(), name='current_team'),
    url(r'^team/(?P<pk>\d+)$', views.Team.as_view(), name='team'),
    url(r'^submit_flag/({})$'.format(UUID_REGEX), views.submit_flag, name='submit_flag'),
]
