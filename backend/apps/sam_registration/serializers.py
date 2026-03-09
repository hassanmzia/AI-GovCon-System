from rest_framework import serializers

from apps.sam_registration.models import SAMContact, SAMRegistration


class SAMContactSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = SAMContact
        fields = [
            "id",
            "registration",
            "role",
            "role_display",
            "name",
            "title",
            "email",
            "phone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SAMRegistrationListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    steps_progress = serializers.SerializerMethodField()

    class Meta:
        model = SAMRegistration
        fields = [
            "id",
            "legal_business_name",
            "uei_number",
            "status",
            "status_display",
            "registration_date",
            "expiration_date",
            "steps_progress",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_steps_progress(self, obj):
        steps = obj.steps_completed or []
        completed = sum(1 for s in steps if s)
        return {"completed": completed, "total": len(steps)}


class SAMRegistrationDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    contacts = SAMContactSerializer(many=True, read_only=True)
    steps_progress = serializers.SerializerMethodField()
    validation_progress = serializers.SerializerMethodField()
    days_until_expiration = serializers.SerializerMethodField()

    class Meta:
        model = SAMRegistration
        fields = [
            "id",
            "owner",
            # Identifiers
            "uei_number",
            "cage_code",
            "tracking_number",
            "ein_number",
            # Entity
            "legal_business_name",
            "physical_address",
            "entity_type",
            # Status
            "status",
            "status_display",
            "registration_date",
            "expiration_date",
            "submitted_date",
            # Progress
            "steps_completed",
            "steps_progress",
            "validation_items",
            "validation_progress",
            "days_until_expiration",
            # Contacts
            "contacts",
            # Notes
            "notes",
            # Timestamps
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_steps_progress(self, obj):
        steps = obj.steps_completed or []
        completed = sum(1 for s in steps if s)
        return {"completed": completed, "total": len(steps)}

    def get_validation_progress(self, obj):
        items = obj.validation_items or {}
        total = len(items)
        checked = sum(1 for v in items.values() if v)
        return {"checked": checked, "total": total}

    def get_days_until_expiration(self, obj):
        if not obj.expiration_date:
            return None
        from django.utils import timezone
        today = timezone.now().date()
        delta = obj.expiration_date - today
        return delta.days


class SAMRegistrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SAMRegistration
        fields = [
            "id",
            "legal_business_name",
            "uei_number",
            "cage_code",
            "tracking_number",
            "ein_number",
            "physical_address",
            "entity_type",
            "status",
            "registration_date",
            "expiration_date",
            "submitted_date",
            "steps_completed",
            "validation_items",
            "notes",
        ]
        read_only_fields = ["id"]
