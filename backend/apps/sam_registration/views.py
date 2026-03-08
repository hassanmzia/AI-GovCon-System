from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import Notification
from apps.sam_registration.models import SAMContact, SAMRegistration
from apps.sam_registration.serializers import (
    SAMContactSerializer,
    SAMRegistrationCreateSerializer,
    SAMRegistrationDetailSerializer,
    SAMRegistrationListSerializer,
)


class SAMRegistrationViewSet(viewsets.ModelViewSet):
    """CRUD for SAM registrations with step/validation tracking."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SAMRegistration.objects.filter(
            owner=self.request.user
        ).prefetch_related("contacts")

    def get_serializer_class(self):
        if self.action == "list":
            return SAMRegistrationListSerializer
        if self.action == "create":
            return SAMRegistrationCreateSerializer
        return SAMRegistrationDetailSerializer

    def perform_create(self, serializer):
        registration = serializer.save(owner=self.request.user)
        # Create default validation items
        if not registration.validation_items:
            registration.validation_items = {
                "name_irs": False,
                "addr_irs": False,
                "ein_verified": False,
                "bank_business": False,
                "entity_type": False,
                "naics_codes": False,
                "reps_certs": False,
                "pocs_added": False,
                "all_sections": False,
            }
            registration.save(update_fields=["validation_items"])

    @action(detail=True, methods=["patch"])
    def update_steps(self, request, pk=None):
        """Update step completion status. Expects: {steps_completed: [bool,...]}"""
        registration = self.get_object()
        steps = request.data.get("steps_completed")
        if not isinstance(steps, list) or len(steps) != 10:
            return Response(
                {"error": "steps_completed must be a list of 10 booleans"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        registration.steps_completed = steps
        registration.save(update_fields=["steps_completed", "updated_at"])
        return Response(SAMRegistrationDetailSerializer(registration).data)

    @action(detail=True, methods=["patch"])
    def update_validation(self, request, pk=None):
        """Update validation checklist. Expects: {validation_items: {id: bool,...}}"""
        registration = self.get_object()
        items = request.data.get("validation_items")
        if not isinstance(items, dict):
            return Response(
                {"error": "validation_items must be a dict"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        registration.validation_items = items
        registration.save(update_fields=["validation_items", "updated_at"])
        return Response(SAMRegistrationDetailSerializer(registration).data)

    @action(detail=True, methods=["post"])
    def check_expiration(self, request, pk=None):
        """Check if registration is expiring soon and create notification if needed."""
        registration = self.get_object()
        if not registration.expiration_date:
            return Response({"warning": False, "message": "No expiration date set"})

        today = timezone.now().date()
        days_left = (registration.expiration_date - today).days

        if days_left < 0:
            registration.status = "expired"
            registration.save(update_fields=["status", "updated_at"])
            Notification.objects.create(
                user=request.user,
                title="SAM Registration Expired",
                message=f"Your SAM registration for {registration.legal_business_name} has expired. Renew immediately to avoid disruption.",
                notification_type="error",
                entity_type="sam_registration",
                entity_id=str(registration.id),
            )
            return Response(
                {"warning": True, "days_left": days_left, "message": "Registration has expired!"}
            )
        elif days_left <= 60:
            Notification.objects.get_or_create(
                user=request.user,
                entity_type="sam_registration",
                entity_id=str(registration.id),
                notification_type="warning",
                defaults={
                    "title": "SAM Registration Expiring Soon",
                    "message": f"Your SAM registration for {registration.legal_business_name} expires in {days_left} days. Start renewal now.",
                },
            )
            return Response(
                {"warning": True, "days_left": days_left, "message": f"Expires in {days_left} days"}
            )

        return Response({"warning": False, "days_left": days_left, "message": "Registration is current"})


class SAMContactViewSet(viewsets.ModelViewSet):
    """CRUD for SAM registration points of contact."""

    serializer_class = SAMContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SAMContact.objects.filter(
            registration__owner=self.request.user
        )
