from django.conf.urls import url

from ctflex.constants import UUID_REGEX
from ctflex import views


app_name = 'ctflex'

urlpatterns = [
    url('^$', views.index, name='index'),
    url(r'^game$', views.game, name='game'),
    url(r'^team$', views.CurrentTeam.as_view(), name='current_team'),
    url(r'^team/(?P<pk>\d+)$', views.Team.as_view(), name='team'),
    url(r'^submit_flag/({})$'.format(UUID_REGEX), views.submit_flag, name='submit_flag'),
    url(r'^start_window$', views.start_window, name='start_window'),
    url(r'^board$', views.board, name='scoreboard')
]
