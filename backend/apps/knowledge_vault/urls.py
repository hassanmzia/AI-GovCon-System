from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.knowledge_vault.views import DocumentTemplateViewSet, KnowledgeDocumentViewSet

router = DefaultRouter()
router.register(r"documents", KnowledgeDocumentViewSet, basename="document")
router.register(r"templates", DocumentTemplateViewSet, basename="document-template")

app_name = "knowledge_vault"

urlpatterns = [
    path("", include(router.urls)),
]
