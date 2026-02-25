import logging
import os

from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Amendment, ComplianceMatrixItem, RFPDocument, RFPRequirement
from .serializers import (
    AmendmentSerializer,
    ComplianceMatrixItemSerializer,
    RFPDocumentDetailSerializer,
    RFPDocumentListSerializer,
    RFPDocumentUploadSerializer,
    RFPRequirementSerializer,
)

logger = logging.getLogger(__name__)


class RFPDocumentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for RFP documents.

    Supports filtering by deal, document_type, and extraction_status.
    Includes custom actions for file upload and AI extraction triggering.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["deal", "document_type", "extraction_status"]
    search_fields = ["title", "file_name"]
    ordering_fields = ["created_at", "updated_at", "title", "version"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            RFPDocument.objects.all()
            .select_related("deal", "parent_document")
            .annotate(
                requirement_count=Count("requirements", distinct=True),
                compliance_item_count=Count("compliance_items", distinct=True),
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return RFPDocumentListSerializer
        if self.action == "upload":
            return RFPDocumentUploadSerializer
        return RFPDocumentDetailSerializer

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
        url_path="upload",
    )
    def upload(self, request):
        """
        Upload an RFP document file.

        Accepts multipart/form-data with the file and metadata fields.
        After successful creation, triggers async text extraction.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"detail": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Populate file metadata from the uploaded file
        file_name = uploaded_file.name
        file_size = uploaded_file.size
        file_ext = os.path.splitext(file_name)[1].lstrip(".").lower()

        document = serializer.save(
            file_name=file_name,
            file_size=file_size,
            file_type=file_ext,
            extraction_status="pending",
        )

        # Trigger async extraction task
        try:
            from .tasks import process_rfp_upload
            process_rfp_upload.delay(str(document.id))
        except Exception:
            logger.warning(
                "Failed to enqueue extraction task for document %s. "
                "Celery may not be running.",
                document.id,
            )

        return Response(
            RFPDocumentDetailSerializer(
                self.get_queryset().get(pk=document.pk)
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="extract")
    def extract(self, request, pk=None):
        """
        Trigger (or re-trigger) AI-powered extraction on the document.

        Sets extraction_status to 'processing' and enqueues the Celery task.
        """
        document = self.get_object()

        if document.extraction_status == "processing":
            return Response(
                {"detail": "Extraction is already in progress."},
                status=status.HTTP_409_CONFLICT,
            )

        document.extraction_status = "processing"
        document.save(update_fields=["extraction_status", "updated_at"])

        try:
            from .tasks import process_rfp_upload
            process_rfp_upload.delay(str(document.id))
        except Exception:
            document.extraction_status = "failed"
            document.save(update_fields=["extraction_status", "updated_at"])
            logger.exception(
                "Failed to enqueue extraction task for document %s", document.id
            )
            return Response(
                {"detail": "Failed to enqueue extraction task."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": "Extraction started.", "extraction_status": "processing"},
            status=status.HTTP_202_ACCEPTED,
        )


class RFPRequirementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve RFP requirements.

    Supports filtering by rfp_document, requirement_type, and category.
    """
    serializer_class = RFPRequirementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["rfp_document", "requirement_type", "category"]
    search_fields = ["requirement_id", "requirement_text", "section_reference"]
    ordering_fields = ["requirement_id", "requirement_type", "created_at"]
    ordering = ["requirement_id"]

    def get_queryset(self):
        return RFPRequirement.objects.all().select_related("rfp_document")


class ComplianceMatrixViewSet(viewsets.ModelViewSet):
    """
    List and update compliance matrix items.

    Supports filtering by rfp_document, compliance_status, and response_status.
    """
    serializer_class = ComplianceMatrixItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["rfp_document", "compliance_status", "response_status"]
    search_fields = [
        "requirement__requirement_id",
        "requirement__requirement_text",
        "proposal_section",
    ]
    ordering_fields = [
        "requirement__requirement_id",
        "compliance_status",
        "response_status",
        "created_at",
    ]
    ordering = ["requirement__requirement_id"]
    # Disallow creation/deletion through this viewset; items are created
    # automatically by the extraction pipeline.
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_queryset(self):
        return (
            ComplianceMatrixItem.objects.all()
            .select_related("rfp_document", "requirement", "response_owner")
        )


class AmendmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve amendments.

    Supports filtering by rfp_document.
    """
    serializer_class = AmendmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["rfp_document", "is_material", "reviewed"]
    search_fields = ["title", "summary"]
    ordering_fields = ["amendment_number", "detected_at", "created_at"]
    ordering = ["amendment_number"]

    def get_queryset(self):
        return Amendment.objects.all().select_related("rfp_document")
