"""Route URLs to Views"""

from django.conf.urls import url, include

from ctflex.constants import APP_NAME, UUID_REGEX
from ctflex import views

app_name = APP_NAME

# TODO(Yatharth): Look into changing links everywhere to pass window if it is there

windowed_urls = [
    # Team
    url(r'^team$', views.CurrentTeam.as_view(), name='current_team'),
    url(r'^team/(?P<pk>\d+)$', views.Team.as_view(), name='team'),

    # State
    url(r'^waiting$', views.waiting, name='waiting'),
    url(r'^inactive$', views.inactive, name='inactive'),
    url(r'^done$', views.done, name='done'),

    # Windowed CTF GETs
    url(r'^game$', views.game, name='game'),
    url(r'^board$', views.board, name='scoreboard'),

    # Windowed CTF POSTs
    url(r'^submit_flag/(?P<prob_id>{})$'.format(UUID_REGEX), views.submit_flag, name='submit_flag'),
    url(r'^start_timer$', views.start_timer, name='start_timer'),
]

urlpatterns = [
    # Non-windowed CTF
    url('^$', views.index, name='index'),
    url(r'^board$', views.board_overall, name='scoreboard_overall'),

    # Auth
    url(r'^login$', views.login, name='login'),
    url(r'^logout$', views.logout, name='logout'),
    url(r'^register$', views.register, name='register'),
    url(r'^register_user$', views.register_user, name='register_user'),

    # Windowed
    url(r'^window(?P<window_id>\d+)/', include(windowed_urls)),
]
