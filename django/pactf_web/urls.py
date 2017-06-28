"""Route URLs to views"""

from django.conf.urls import url

from ctflex.urls import WINDOW_CODE_TOKEN

from pactf_web import views
from pactf_web.constants import APP_NAME

app_name = APP_NAME

urlpatterns = [

    # CTFlex overrides
    url(r'^scoreboard/{}?$'.format(WINDOW_CODE_TOKEN), views.board, name='scoreboard'),
    url(r'^winners/$', views.winners, name='winners'),

]
