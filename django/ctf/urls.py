from django.conf.urls import url

from ctf import views

UUID_REGEX = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

app_name = 'ctf'

urlpatterns = [
    url('^$', views.index, name='index'),
    url(r'^game$', views.game, name='game'),
    url(r'^team$', views.CurrentTeam.as_view(), name='current_team'),
    url(r'^team/(?P<pk>\d+)$', views.Team.as_view(), name='team'),
    url(r'^submit_flag/({})'.format(UUID_REGEX), views.submit_flag, name='submit_flag'),
]
