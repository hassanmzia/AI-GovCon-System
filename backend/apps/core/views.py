from django.http import JsonResponse
from rest_framework import viewsets  # noqa: F401


def health_check(request):
    return JsonResponse({"status": "ok"})
