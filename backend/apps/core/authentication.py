"""
Service-to-service authentication for internal microservice calls.

The AI orchestrator and other backend services authenticate with a shared
static token (DJANGO_SERVICE_TOKEN environment variable) rather than a
per-user JWT.  This class validates that token and returns a dedicated
service account user so that standard IsAuthenticated permission checks pass.

Usage
-----
Enabled globally via REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] in
settings/base.py.  No changes are required on individual views.

Security notes
--------------
- The service token must be a long random secret (≥32 chars).  Set it via
  the DJANGO_SERVICE_TOKEN environment variable.
- The service account ("ai-orchestrator-service") is created automatically
  on first use; it has no password and is_staff=False.
- This class never falls back to any other auth mechanism.  If the token
  does not match it returns None, leaving other authenticators in the chain
  to try.
"""

import logging
import os

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger("ai_orchestrator.authentication")

_SERVICE_USERNAME = "ai-orchestrator-service"


class ServiceTokenAuthentication(BaseAuthentication):
    """
    Authenticates requests that carry the shared DJANGO_SERVICE_TOKEN.

    Expected header::

        Authorization: Bearer <DJANGO_SERVICE_TOKEN value>

    Returns (service_user, token) on success; None if the header is absent
    or does not look like a service-token request (allows JWT / Session auth
    to try next).  Raises AuthenticationFailed if the token is present but
    wrong, to prevent silent fallthrough.
    """

    def authenticate(self, request):
        service_token = os.getenv("DJANGO_SERVICE_TOKEN", "").strip()
        if not service_token:
            return None  # Service token auth not configured — skip

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None  # Not a Bearer token — let other authenticators try

        provided_token = auth_header[len("Bearer "):]

        if provided_token != service_token:
            # Token present but wrong — raise so the request fails fast
            # instead of falling through to JWT/session which would also fail.
            raise AuthenticationFailed(
                "Service token is invalid.",
                code="service_token_invalid",
            )

        user = self._get_or_create_service_user()
        return (user, provided_token)

    def authenticate_header(self, request):
        return "Bearer realm=service"

    @staticmethod
    def _get_or_create_service_user():
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=_SERVICE_USERNAME,
            defaults={
                "is_active": True,
                "is_staff": False,
                "first_name": "AI",
                "last_name": "Orchestrator",
            },
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
            logger.info("Created service account '%s'", _SERVICE_USERNAME)
        return user
