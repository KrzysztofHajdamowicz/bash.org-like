from django.urls import path
from . import views

urlpatterns = [
    path("", views.index_view, name="index_view"),
    path("login/", views.login_user, name="login_user"),
    path("manage/", views.quote_manage, name="quote_manage"),
    path("quote/show", views.accepted_list, name="accepted_list"),
    path("quote/best", views.best_list, name="best_list"),
    path("trash/show", views.trash_list, name="trash_list"),
    path("quote/<int:quote_id>/", views.quote_view, name="quote_view"),
    path("quote/accept/<int:quote_id>/", views.quote_accept, name="quote_accept"),
    path("quote/reject/<int:quote_id>/", views.quote_reject, name="quote_reject"),
    path("quote/delete/<int:quote_id>/", views.quote_delete, name="quote_delete"),
    path("quote/vote_up/<int:quote_id>/", views.quote_vote_up, name="quote_vote_up"),
    path("quote/vote_down/<int:quote_id>/", views.quote_vote_down, name="quote_vote_down"),
    path("quote/add", views.quote_add, name="quote_add"),
    path("quote/ajax", views.quote_ajax, name="quote_ajax"),
]
