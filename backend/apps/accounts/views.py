from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveUpdateAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserAdminUpdateSerializer,
    UserCreateSerializer,
    UserProfileSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(CreateAPIView):
    """Register a new user account."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(RetrieveUpdateAPIView):
    """Retrieve or update the current user's profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


class UserListView(ListCreateAPIView):
    """List all users or create a new user (admin only, except first user)."""

    queryset = User.objects.all()

    def get_permissions(self):
        """
        Allow anyone to create the first user as admin (bootstrap).
        After that, only admins can list or create users.
        """
        if self.request.method == "POST" and not User.objects.exists():
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer


class UserAdminDetailView(RetrieveUpdateDestroyAPIView):
    """Retrieve or update a specific user by ID (admin only)."""

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserAdminUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class ChangePasswordView(UpdateAPIView):
    """Change the current user's password."""

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"detail": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )


class MFASetupView(CreateAPIView):
    """Setup MFA for the current user."""

    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Initialize MFA setup and return QR code."""
        # TODO: Implement actual TOTP setup with pyotp and QR code generation
        # For now, just mark MFA as enabled
        user = request.user
        user.is_mfa_enabled = True
        user.save()
        return Response(
            {
                "detail": "MFA setup initiated. Please scan the QR code with your authenticator app.",
                "qr_code": "placeholder",  # In production, generate actual QR code
            },
            status=status.HTTP_200_OK,
        )


class MFADisableView(CreateAPIView):
    """Disable MFA for the current user."""

    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Disable MFA."""
        user = request.user
        user.is_mfa_enabled = False
        user.save()
        return Response(
            {"detail": "MFA has been disabled."},
            status=status.HTTP_200_OK,
        )


class UserMeView(RetrieveUpdateAPIView):
    """Retrieve or update the current authenticated user."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
