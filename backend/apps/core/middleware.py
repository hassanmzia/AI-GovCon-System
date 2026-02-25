import json
import logging
import re

from .models import AuditLog

logger = logging.getLogger(__name__)

# Pattern to extract entity_type and entity_id from URL paths
# e.g. /api/v1/deals/abc-123/ -> entity_type="deals", entity_id="abc-123"
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
    "/health",
    "/healthz",
    "/readyz",
    "/livez",
    "/favicon.ico",
    "/media/",
)

# Maximum body size to capture (bytes) — prevents logging huge uploads
_MAX_BODY_CAPTURE = 16_384  # 16 KB


class AuditMiddleware:
    """Automatically log all POST/PUT/PATCH/DELETE API requests to AuditLog.

    Captures:
    - user: the authenticated user (or None for anonymous requests)
    - action: create / update / delete (derived from HTTP method)
    - entity_type: extracted from the URL path
    - old_value: previous state for update operations (from response body)
    - new_value: request body payload
    - ip_address: client IP (respects X-Forwarded-For)
    - user_agent: HTTP User-Agent header

    Skips health check and static file URLs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capture request body before it is consumed by the view
        request_body = self._capture_request_body(request)

        response = self.get_response(request)
        self._process_response(request, response, request_body)
        return response

    def _process_response(self, request, response, request_body):
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

        # Parse new_value from the request body
        new_value = self._parse_json_body(request_body)

        # Parse old_value from response for update operations
        # For updates the response often contains the previous or updated resource
        old_value = None
        if action == "update":
            old_value = self._extract_old_value(response)

        try:
            AuditLog.objects.create(
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
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

    @staticmethod
    def _capture_request_body(request) -> bytes:
        """Read the request body for later logging.

        Only captures bodies within the size limit and only for mutating methods.
        """
        if request.method not in HTTP_METHOD_TO_ACTION:
            return b""

        # Skip if path is excluded
        if any(request.path.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            return b""

        try:
            body = request.body
            if len(body) > _MAX_BODY_CAPTURE:
                return b""
            return body
        except Exception:
            return b""

    @staticmethod
    def _parse_json_body(body: bytes) -> dict | None:
        """Attempt to parse bytes as JSON. Returns None on failure."""
        if not body:
            return None
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                # Strip potentially sensitive fields
                sanitized = {
                    k: v for k, v in parsed.items()
                    if k.lower() not in ("password", "token", "secret", "api_key", "authorization")
                }
                return sanitized
            return {"_data": parsed}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    @staticmethod
    def _extract_old_value(response) -> dict | None:
        """Extract the resource state from the response body for update operations.

        For DRF responses the response.data attribute holds the serialized
        representation *before* rendering. This serves as the old_value proxy.
        """
        # Try DRF response.data first (pre-render)
        if hasattr(response, "data") and isinstance(response.data, dict):
            return response.data

        # Fallback: parse response content
        content_type = response.get("Content-Type", "")
        if "application/json" not in content_type:
            return None

        try:
            content = response.content
            if len(content) > _MAX_BODY_CAPTURE:
                return None
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        return None
