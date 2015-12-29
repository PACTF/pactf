from django.conf.urls import url, include

from . import views


app_name = 'ctf'

urlpatterns = [
    url('^$', views.index, name='index'),
    url(r'^game$', views.game, name='game'),
    url(r'^team$', views.CurrentTeam.as_view(), name='current_team'),
    url(r'^team/(?P<pk>\d+)$', views.Team.as_view(), name='team'),
    url(r'^submit_flag/(\d+)', views.submit_flag, name='submit_flag'),
]
