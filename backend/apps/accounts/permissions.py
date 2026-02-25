from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Allow access only to users with the admin role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsExecutiveOrAbove(BasePermission):
    """Allow access to admin or executive roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "executive")
        )


class IsCaptureManager(BasePermission):
    """Allow access to admin, executive, or capture_manager roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "executive", "capture_manager")
        )


class IsProposalManager(BasePermission):
    """Allow access to admin, executive, or proposal_manager roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "executive", "proposal_manager")
        )


class ReadOnly(BasePermission):
    """Allow read-only access (safe HTTP methods only)."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsViewerReadOnly(BasePermission):
    """Allow viewers read-only access, all others full access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Non-viewers have full access
        if request.user.role != "viewer":
            return True

        # Viewers can only read
        return request.method in SAFE_METHODS
