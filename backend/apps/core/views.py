from django.http import JsonResponse
from rest_framework import viewsets  # noqa: F401
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


def health_check(request):
    return JsonResponse({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def llm_settings(request):
    """Return the current LLM provider configuration and available providers."""
    from apps.core.llm_provider import get_provider_info

    info = get_provider_info()
    return Response(info)
