from django.http import JsonResponse
from rest_framework import viewsets  # noqa: F401
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response


def health_check(request):
    return JsonResponse({"status": "ok"})


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def llm_settings(request):
    """GET: return current config. PUT: update provider/model selection."""
    from apps.core.llm_provider import get_provider_info, update_settings

    if request.method == "GET":
        return Response(get_provider_info())

    # PUT — update LLM provider settings
    provider = request.data.get("provider", "").strip().lower()
    model = request.data.get("model", "").strip()
    ollama_base_url = request.data.get("ollama_base_url", "").strip()

    if not provider:
        return Response({"error": "provider is required"}, status=400)
    if not model:
        return Response({"error": "model is required"}, status=400)

    try:
        info = update_settings(provider, model, ollama_base_url)
        return Response(info)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
