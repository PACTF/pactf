from django.conf.urls import url, include

from ctflex.constants import UUID_REGEX
from ctflex import views


app_name = 'ctflex'


# TODO(Yatharth): Look into changing links everywhere to pass window if it is there
# TODO(Yatharth): Remember last selected window in a session?

windowed_urls = [
    url(r'^team$', views.CurrentTeam.as_view(), name='current_team'),
    url(r'^team/(?P<pk>\d+)$', views.Team.as_view(), name='team'),

    url(r'^game$', views.game, name='game'),
    url(r'^board$', views.board, name='scoreboard'),

    url(r'^waiting', views.waiting, name='waiting'),
    url(r'^inactive', views.inactive, name='inactive'),
    url(r'^done', views.done, name='done'),

    url(r'^submit_flag/(?P<prob_id>{})$'.format(UUID_REGEX), views.submit_flag, name='submit_flag'),
    url(r'^start_timer$', views.start_timer, name='start_timer'),
]


urlpatterns = [
    url('^$', views.index, name='index'),
    url(r'^window(?P<window_id>\d+)/', include(windowed_urls)),
    url(r'^', include(windowed_urls), {'window_id': None})
]
