from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "polls"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
    path("register/", views.register_request, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="polls/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="polls:index"), name="logout"),
    path("create/", views.create_poll, name="create_poll"),
    path("settings/", views.account_settings, name="settings"),
    path("my-polls/", views.my_polls, name="my_polls"),
    path("<int:question_id>/toggle-privacy/", views.toggle_privacy, name="toggle_privacy"),
]