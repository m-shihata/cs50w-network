
from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    # Views
    path("home", views.home, name="home"),
    path("following", views.following, name="following"),
    path("<str:username>", views.profile, name="profile"),

    # API routes
    path("api/compose/post", views.compose, name="compose"),
    path("api/edit/post/<int:id>", views.edit, name="edit"),
    path("api/toggle/post/<int:id>/like", views.like_toggle, name="like"),
    path("api/follow/<str:username>", views.follow_toggle, name="follow"),
    path("api/home/posts/<int:page>", views.home_posts, name="home_posts"),
    path("api/profile/<str:username>/info", views.profile_info, name="profile_info"),
    path("api/profile/<str:username>/in_Following", views.in_Following, name="in_Following"),
    path("api/profile/<str:username>/posts/<int:page>", views.profile_posts, name="profile_posts"),
    path("api/following/posts/<int:page>", views.following_posts, name="following_posts"),
]

