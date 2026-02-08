from django.urls import path
from .views import register_view,login_view,dashboard,home_view,logout_view


app_name = "accounts"

urlpatterns = [
    path("", home_view, name="home"),
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard")
]