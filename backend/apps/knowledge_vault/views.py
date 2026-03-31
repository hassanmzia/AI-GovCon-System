from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.knowledge_vault.models import DocumentTemplate, KnowledgeDocument
from apps.knowledge_vault.serializers import (
    DocumentTemplateDetailSerializer,
    DocumentTemplateListSerializer,
    KnowledgeDocumentSerializer,
)


class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    """Knowledge vault documents management."""

    queryset = KnowledgeDocument.objects.all()
    serializer_class = KnowledgeDocumentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set author to current user on creation."""
        serializer.save(author=self.request.user)

    def get_queryset(self):
        """Filter by public documents or documents authored by user."""
        queryset = KnowledgeDocument.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status="approved") & (
                queryset.filter(is_public=True) | queryset.filter(author=self.request.user)
            )
        return queryset


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """
    Unified template library — CRUD, file upload, rendering, and
    download tracking for all GovCon document templates.
    """

    queryset = DocumentTemplate.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "file_format", "is_active", "is_default", "source"]
    search_fields = ["name", "description", "tags"]
    ordering_fields = ["name", "category", "created_at", "usage_count"]
    ordering = ["category", "name"]

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentTemplateListSerializer
        return DocumentTemplateDetailSerializer

    def perform_create(self, serializer):
        file_obj = serializer.validated_data.get("file")
        file_size = file_obj.size if file_obj else 0
        serializer.save(uploaded_by=self.request.user, file_size=file_size)

    def perform_update(self, serializer):
        file_obj = serializer.validated_data.get("file")
        if file_obj:
            serializer.save(file_size=file_obj.size)
        else:
            serializer.save()

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        """Mark this template as the default for its category."""
        template = self.get_object()
        DocumentTemplate.objects.filter(
            category=template.category, is_default=True
        ).update(is_default=False)
        template.is_default = True
        template.save(update_fields=["is_default", "updated_at"])
        return Response({"status": "default set", "id": str(template.id)})

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """Duplicate a template with a new version."""
        original = self.get_object()
        new_version = request.data.get("version", f"{original.version}-copy")
        clone = DocumentTemplate.objects.create(
            name=f"{original.name} (Copy)",
            description=original.description,
            category=original.category,
            file_format=original.file_format,
            file=original.file,
            file_size=original.file_size,
            variables=original.variables,
            version=new_version,
            source=original.source,
            tags=original.tags,
            is_active=True,
            is_default=False,
            uploaded_by=request.user,
        )
        serializer = DocumentTemplateDetailSerializer(clone, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def track_download(self, request, pk=None):
        """Increment download/usage counter."""
        template = self.get_object()
        template.usage_count += 1
        template.save(update_fields=["usage_count", "updated_at"])
        return Response({"usage_count": template.usage_count})

    @action(detail=True, methods=["post"])
    def render(self, request, pk=None):
        """
        Render a DOCX/TXT template with provided variable values.

        POST body: {"variables": {"company_name": "Acme Corp", ...}}
        Returns: rendered file as download.
        """
        from django.http import FileResponse

        from apps.knowledge_vault.services.template_renderer import render_template_to_file

        template = self.get_object()
        context = request.data.get("variables", {})

        if not isinstance(context, dict):
            return Response(
                {"error": "variables must be a JSON object"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rendered_file = render_template_to_file(template, context)
        except (ImportError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"error": f"Rendering failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Track usage
        template.usage_count += 1
        template.save(update_fields=["usage_count", "updated_at"])

        return FileResponse(
            rendered_file,
            as_attachment=True,
            filename=rendered_file.name,
        )

    @action(detail=True, methods=["get"])
    def extract_variables(self, request, pk=None):
        """Extract template variables from the uploaded file."""
        from apps.knowledge_vault.services.template_renderer import (
            extract_variables_from_docx,
        )

        template = self.get_object()
        if not template.file:
            return Response({"variables": [], "note": "No file uploaded"})

        if template.file_format == "docx":
            try:
                variables = extract_variables_from_docx(template.file)
            except ImportError:
                return Response(
                    {"error": "docxtpl not installed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            variables = template.variables or []

        return Response({"variables": variables})
