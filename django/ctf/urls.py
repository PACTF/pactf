from django.conf.urls import url

from . import views

# TODO(yatharth): Do we actually need this?
app_name = 'ctf'

urlpatterns = (
    url(r'^team/(?P<pk>\d+)$', views.TeamDetailView.as_view(), name='team'),
)
