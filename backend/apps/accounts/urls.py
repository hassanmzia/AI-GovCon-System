from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    ChangePasswordView,
    MFADisableView,
    MFASetupView,
    RegisterView,
    UserAdminDetailView,
    UserListView,
    UserMeView,
    UserProfileView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("me/", UserMeView.as_view(), name="user-me"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<str:pk>/", UserAdminDetailView.as_view(), name="user-detail"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("mfa/setup/", MFASetupView.as_view(), name="mfa-setup"),
    path("mfa/disable/", MFADisableView.as_view(), name="mfa-disable"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
