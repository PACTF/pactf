from django.conf.urls import url

from . import views


app_name = 'ctf'

urlpatterns = (
    url('^$', views.index, name='index'),
    url(r'^team/(?P<pk>\d+)$', views.TeamDetailView.as_view(), name='team'),
)
