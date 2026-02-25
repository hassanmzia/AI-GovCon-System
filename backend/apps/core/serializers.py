from rest_framework import serializers

from .models import AITraceLog, AuditLog, Notification


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_email",
            "action",
            "entity_type",
            "entity_id",
            "old_value",
            "new_value",
            "ip_address",
            "user_agent",
            "timestamp",
        ]
        read_only_fields = fields


class AITraceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITraceLog
        fields = [
            "id",
            "agent_name",
            "deal",
            "action",
            "prompt",
            "tool_calls",
            "retrieved_sources",
            "output",
            "approval_status",
            "cost_usd",
            "latency_ms",
            "model_name",
            "trace_id",
            "timestamp",
        ]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "title",
            "message",
            "notification_type",
            "entity_type",
            "entity_id",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "title",
            "message",
            "notification_type",
            "entity_type",
            "entity_id",
            "created_at",
        ]
