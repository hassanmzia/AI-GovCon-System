from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.knowledge_vault.views import KnowledgeDocumentViewSet

router = DefaultRouter()
router.register(r"documents", KnowledgeDocumentViewSet, basename="document")

app_name = "knowledge_vault"

urlpatterns = [
    path("", include(router.urls)),
]
