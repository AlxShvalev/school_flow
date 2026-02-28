from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    # Auth
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Profile
    path("profile/", views.UserProfileDetailView.as_view(), name="profile_detail"),
    path(
        "profile/<uuid:pk>/",
        views.UserProfileDetailByIdView.as_view(),
        name="profile_detail_by_id",
    ),
    path(
        "profiles/<uuid:pk>/edit/",
        views.UserProfileUpdateView.as_view(),
        name="profile_edit",
    ),
    path(
        "profiles/create/",
        views.ProfileCreateView.as_view(),
        name="profile_create",
    ),
    path(
        "profiles/",
        views.ProfileListView.as_view(),
        name="profile_list",
    ),
    # Invites (admin)
    path("invites/", views.InviteListView.as_view(), name="invite_list"),
    path("invites/create/", views.InviteCreateView.as_view(), name="invite_create"),
    path(
        "invites/<uuid:pk>/edit/",
        views.InviteUpdateView.as_view(),
        name="invite_edit",
    ),
    path(
        "invites/<uuid:pk>/delete/",
        views.InviteDeleteView.as_view(),
        name="invite_delete",
    ),
    # Registration by invite
    path(
        "invites/<uuid:token>/register/",
        views.InviteRegisterView.as_view(),
        name="invite_register",
    ),
    # Users management (admin)
    path("list/", views.UserListView.as_view(), name="user_list"),
    path(
        "<uuid:pk>/toggle_active/",
        views.UserToggleActiveView.as_view(),
        name="user_toggle_active",
    ),
    # Home
    path("", views.home_view, name="home"),
]
