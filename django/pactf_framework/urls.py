from django.conf.urls import url

from . import views

# TODO(yatharth): Do we actually need this?
app_name = 'framework'

urlpatterns = (
    url(r'^team/(?P<pk>\d+)$', views.TeamDetailView.as_view(), name='team'),
)
