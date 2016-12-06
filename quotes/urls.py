from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index_view, name='index_view'),
    url(r'^login/$', views.login_user, name='login_user'),
    url(r'^manage/$', views.quote_manage, name='quote_manage'),
    url(r'^quote/show$', views.accepted_list, name='accepted_list'),
    url(r'^trash/show$', views.trash_list, name='trash_list'),
    url(r'^quote/(?P<quote_id>[0-9]+)/$', views.quote_view, name='quote_view'),
    url(r'^quote/accept/(?P<quote_id>[0-9]+)/$', views.quote_accept, name='quote_accept'),
    url(r'^quote/reject/(?P<quote_id>[0-9]+)/$', views.quote_reject, name='quote_reject'),
    url(r'^quote/delete/(?P<quote_id>[0-9]+)/$', views.quote_delete, name='quote_delete'),
    url(r'^quote/vote_up/(?P<quote_id>[0-9]+)/$', views.quote_vote_up, name='quote_vote_up'),
    url(r'^quote/vote_down/(?P<quote_id>[0-9]+)/$', views.quote_vote_down, name='quote_vote_down'),
    url(r'^quote/add$', views.quote_add, name='quote_add'),
]