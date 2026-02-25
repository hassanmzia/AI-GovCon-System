import logging
import re

from .models import AuditLog

logger = logging.getLogger(__name__)

# Pattern to extract entity_type and entity_id from URL paths
# e.g. /api/v1/deals/abc-123/ → entity_type="deals", entity_id="abc-123"
ENTITY_PATH_RE = re.compile(
    r"/api/(?:v\d+/)?(?P<entity_type>[a-z_-]+)/(?P<entity_id>[0-9a-f-]+)"
)

HTTP_METHOD_TO_ACTION = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

SKIP_PATH_PREFIXES = (
    "/static/",
    "/admin/jsi18n/",
)


class AuditMiddleware:
    """Automatically log mutating API requests to AuditLog."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._process_response(request, response)
        return response

    def _process_response(self, request, response):
        # Only log mutating methods
        if request.method not in HTTP_METHOD_TO_ACTION:
            return

        # Skip excluded paths
        if any(request.path.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            return

        # Only log successful responses (2xx)
        if not (200 <= response.status_code < 300):
            return

        # Resolve user
        user = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user = request.user

        # Try to extract entity info from the URL
        entity_type = ""
        entity_id = ""
        match = ENTITY_PATH_RE.search(request.path)
        if match:
            entity_type = match.group("entity_type")
            entity_id = match.group("entity_id")
        else:
            # For POST (create) the entity_type is the last path segment
            parts = [p for p in request.path.strip("/").split("/") if p]
            if parts:
                entity_type = parts[-1]

        action = HTTP_METHOD_TO_ACTION[request.method]

        ip_address = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            AuditLog.objects.create(
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception:
            logger.exception("Failed to create audit log entry")

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP, respecting X-Forwarded-For behind a proxy."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
