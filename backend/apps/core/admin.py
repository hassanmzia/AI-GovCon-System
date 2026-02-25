from django.contrib import admin

from .models import AITraceLog, AuditLog, Notification


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "user",
        "action",
        "entity_type",
        "entity_id",
        "ip_address",
    )
    list_filter = ("action", "entity_type", "timestamp")
    search_fields = ("entity_type", "entity_id", "user__email")
    readonly_fields = (
        "id",
        "user",
        "action",
        "entity_type",
        "entity_id",
        "old_value",
        "new_value",
        "ip_address",
        "user_agent",
        "timestamp",
        "created_at",
        "updated_at",
    )
    ordering = ("-timestamp",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AITraceLog)
class AITraceLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "agent_name",
        "action",
        "deal",
        "approval_status",
        "cost_usd",
        "latency_ms",
    )
    list_filter = ("agent_name", "approval_status", "timestamp")
    search_fields = ("agent_name", "action", "trace_id")
    readonly_fields = (
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
        "created_at",
        "updated_at",
    )
    ordering = ("-timestamp",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "title",
        "notification_type",
        "is_read",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__email")
    ordering = ("-created_at",)
