from rest_framework import serializers

from apps.sba_certifications.models import NAICSCode, SBACertification


class SBACertificationSerializer(serializers.ModelSerializer):
    cert_type_display = serializers.CharField(
        source="get_cert_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    days_until_expiration = serializers.SerializerMethodField()

    class Meta:
        model = SBACertification
        fields = [
            "id",
            "cert_type",
            "cert_type_display",
            "status",
            "status_display",
            "certification_number",
            "application_date",
            "certification_date",
            "expiration_date",
            "renewal_date",
            "application_steps",
            "documents_uploaded",
            "description",
            "requirements",
            "notes",
            "days_until_expiration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_days_until_expiration(self, obj):
        if not obj.expiration_date:
            return None
        from django.utils import timezone

        delta = obj.expiration_date - timezone.now().date()
        return delta.days


class NAICSCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NAICSCode
        fields = [
            "id",
            "code",
            "title",
            "size_standard",
            "is_primary",
            "qualifies_small",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
