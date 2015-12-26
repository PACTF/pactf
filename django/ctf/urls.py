from django.conf.urls import url

from . import views


app_name = 'ctf'

urlpatterns = [
    url('^$', views.index, name='index'),
    url(r'^game$', views.game, name='game'),
    url(r'^team/(?P<pk>\d+)$', views.TeamDetailView.as_view(), name='team'),
    url(r'^submit_flag/(\d+)', views.submit_flag, name='submit_flag')
]
