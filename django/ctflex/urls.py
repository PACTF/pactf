"""Route URLs to Views"""

from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.conf import settings

from ctflex.views import anonyomous_users_only
from pactf.constants import VERBOSE_NAME
from ctflex.constants import APP_NAME, UUID_REGEX
from ctflex import views

app_name = APP_NAME

windowed_urls = [
    # State
    url(r'^waiting/$', views.waiting, name='waiting'),
    url(r'^inactive/$', views.inactive, name='inactive'),
    url(r'^done/$', views.done, name='done'),

    # Windowed CTF GETs
    url(r'^game/$', views.game, name='game'),
    url(r'^board/$', views.board, name='scoreboard'),

    # Windowed CTF POSTs
    url(r'^submit_flag/(?P<prob_id>{})/$'.format(UUID_REGEX), views.submit_flag, name='submit_flag'),
    url(r'^start_timer/$', views.start_timer, name='start_timer'),
]

auth_urls = [
    url(r'^login/$', anonyomous_users_only()(auth_views.login), name='login', kwargs={
        'template_name': 'ctflex/auth/login.html'
    }),

    url(r'^logout/$', auth_views.logout, name='logout', kwargs={
        'next_page': 'ctflex:logout_done',
    }),

    url(r'^logout/done/$', views.logout_done, name='logout_done'),

    url(r'^password_change/$', auth_views.password_change, name='password_change', kwargs={
        'template_name': 'ctflex/auth/password_change.html',
        'post_change_redirect': 'ctflex:password_change_done',
    }),

    url(r'^password_change/done/$', views.password_change_done, name='password_change_done'),

    url(r'^password_reset/$', auth_views.password_reset, name='password_reset', kwargs={
        'template_name': 'ctflex/auth/password_reset.html',
        'email_template_name': 'ctflex/auth/password_reset_email.txt',
        'subject_template_name': 'ctflex/auth/password_reset_email_subject.txt',
        'post_reset_redirect': 'ctflex:password_reset_done',
        'extra_email_context': {
            'support_email': settings.SUPPORT_EMAIL,
            'sitename': VERBOSE_NAME,
        },
    }),

    url(r'^password_reset/done/$', auth_views.password_reset_done, name='password_reset_done', kwargs={
        'template_name': 'ctflex/auth/password_reset_done.html',
    }),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm', kwargs={
            'template_name': 'ctflex/auth/password_reset_confirm.html',
            'post_reset_redirect': 'ctflex:password_reset_complete',
        }),

    url(r'^reset/done/$', views.password_reset_complete, name='password_reset_complete'),

    url(r'^register/$', views.register, name='register'),
]

non_windowed_urls = [
    url(r'^board/overall$', views.board_overall, name='scoreboard_overall'),

    url(r'^team/$', views.CurrentTeam.as_view(), name='current_team'),
    url(r'^team/(?P<pk>\d+)$', views.Team.as_view(), name='team'),
]

urlpatterns = [
    url('^$', views.index, name='index'),

    url(r'^', include(
        auth_urls + non_windowed_urls + windowed_urls
    )),

    url(r'^window(?P<window_id>\d+)/', include(
        non_windowed_urls + windowed_urls
    )),
]
