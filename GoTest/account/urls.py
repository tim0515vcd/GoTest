from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from account.views import (
    ProfileView,
    ChangePasswordPostView,
    UserListView,
    UserPostView,
    RoleListView,
    RoleView,
)

urlpatterns = [
    path("user", UserListView.as_view(), name="userlist"),
    path("user/<int:pk>", UserPostView.as_view(), name="user"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("changepassword", ChangePasswordPostView.as_view(), name="changepassword"),
    path("role", RoleListView.as_view(), name="rolelist"),
    path("role/<int:pk>", RoleView.as_view(), name="role"),
]
