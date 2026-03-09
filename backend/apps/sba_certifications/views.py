from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.sba_certifications.models import NAICSCode, SBACertification
from apps.sba_certifications.serializers import (
    NAICSCodeSerializer,
    SBACertificationSerializer,
)


class SBACertificationViewSet(viewsets.ModelViewSet):
    serializer_class = SBACertificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SBACertification.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="initialize")
    def initialize_certifications(self, request):
        """Create all 8 certification types for the user if they don't exist."""
        created = []
        for cert_type, _ in SBACertification.CERT_TYPE_CHOICES:
            obj, was_created = SBACertification.objects.get_or_create(
                owner=request.user,
                cert_type=cert_type,
                defaults={"status": "not_applicable"},
            )
            if was_created:
                created.append(cert_type)

        certs = SBACertification.objects.filter(owner=request.user)
        serializer = self.get_serializer(certs, many=True)
        return Response(
            {"initialized": created, "certifications": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="update-steps")
    def update_steps(self, request, pk=None):
        """Update application steps for a certification."""
        cert = self.get_object()
        steps = request.data.get("application_steps")
        if steps is None:
            return Response(
                {"error": "application_steps required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cert.application_steps = steps
        cert.save(update_fields=["application_steps", "updated_at"])
        return Response(self.get_serializer(cert).data)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Return certification summary statistics."""
        certs = SBACertification.objects.filter(owner=request.user)
        total = certs.count()
        certified = certs.filter(status="certified").count()
        in_progress = certs.filter(status__in=["in_progress", "applied", "under_review"]).count()
        eligible = certs.filter(status="eligible").count()
        return Response(
            {
                "total": total,
                "certified": certified,
                "in_progress": in_progress,
                "eligible": eligible,
            }
        )


class NAICSCodeViewSet(viewsets.ModelViewSet):
    serializer_class = NAICSCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NAICSCode.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, pk=None):
        """Set this NAICS code as the primary one."""
        naics = self.get_object()
        naics.is_primary = True
        naics.save()
        return Response(self.get_serializer(naics).data)
