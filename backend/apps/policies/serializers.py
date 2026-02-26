from rest_framework import serializers
from .models import (
    AIAutonomyPolicy,
    AIIncident,
    BusinessPolicy,
    PolicyApproval,
    PolicyEnforcementLog,
    PolicyEvaluation,
    PolicyException,
    PolicyRule,
)


class PolicyRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyRule
        fields = [
            "id",
            "policy",
            "rule_name",
            "field_path",
            "operator",
            "threshold_value",
            "threshold_json",
            "error_message",
            "warning_message",
            "is_blocking",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BusinessPolicySerializer(serializers.ModelSerializer):
    created_by_username = serializers.SerializerMethodField(read_only=True)
    rules = PolicyRuleSerializer(many=True, read_only=True)

    class Meta:
        model = BusinessPolicy
        fields = [
            "id",
            "name",
            "description",
            "policy_type",
            "scope",
            "conditions",
            "actions",
            "is_active",
            "priority",
            "effective_date",
            "expiry_date",
            "version",
            "created_by",
            "created_by_username",
            "rules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by_username", "rules", "created_at", "updated_at"]

    def get_created_by_username(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def validate(self, attrs):
        effective_date = attrs.get("effective_date")
        expiry_date = attrs.get("expiry_date")
        if effective_date and expiry_date and expiry_date < effective_date:
            raise serializers.ValidationError(
                {"expiry_date": "Expiry date must be on or after the effective date."}
            )
        return attrs


class PolicyEvaluationSerializer(serializers.ModelSerializer):
    policy_name = serializers.SerializerMethodField(read_only=True)
    deal_title = serializers.SerializerMethodField(read_only=True)
    resolved_by_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PolicyEvaluation
        fields = [
            "id",
            "policy",
            "policy_name",
            "deal",
            "deal_title",
            "evaluated_at",
            "outcome",
            "triggered_rules",
            "recommendations",
            "auto_resolved",
            "resolved_by",
            "resolved_by_username",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "policy_name",
            "deal_title",
            "evaluated_at",
            "resolved_by_username",
            "created_at",
        ]

    def get_policy_name(self, obj):
        return obj.policy.name if obj.policy_id else None

    def get_deal_title(self, obj):
        if obj.deal_id:
            deal = obj.deal
            return getattr(deal, "title", None) or getattr(deal, "name", str(deal))
        return None

    def get_resolved_by_username(self, obj):
        if obj.resolved_by:
            return obj.resolved_by.get_full_name() or obj.resolved_by.username
        return None


class PolicyExceptionSerializer(serializers.ModelSerializer):
    policy_name = serializers.SerializerMethodField(read_only=True)
    deal_title = serializers.SerializerMethodField(read_only=True)
    approved_by_username = serializers.SerializerMethodField(read_only=True)
    requested_by_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PolicyException
        fields = [
            "id",
            "policy",
            "policy_name",
            "deal",
            "deal_title",
            "reason",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "expires_at",
            "status",
            "requested_by",
            "requested_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "policy_name",
            "deal_title",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "requested_by_username",
            "created_at",
            "updated_at",
        ]

    def get_policy_name(self, obj):
        return obj.policy.name if obj.policy_id else None

    def get_deal_title(self, obj):
        if obj.deal_id:
            deal = obj.deal
            return getattr(deal, "title", None) or getattr(deal, "name", str(deal))
        return None

    def get_approved_by_username(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.username
        return None

    def get_requested_by_username(self, obj):
        if obj.requested_by:
            return obj.requested_by.get_full_name() or obj.requested_by.username
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["requested_by"] = request.user
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# AI Autonomy Governance serializers
# ---------------------------------------------------------------------------


class AIAutonomyPolicySerializer(serializers.ModelSerializer):
    """Full serializer for the versioned AI autonomy policy bundle."""

    created_by_username = serializers.SerializerMethodField(read_only=True)
    approved_by_username = serializers.SerializerMethodField(read_only=True)
    # Frontend compat: expose autonomy_level also as 'level'
    level = serializers.IntegerField(source="autonomy_level", read_only=True)
    # Flatten commonly-used policy_json sub-fields for the dashboard
    pricing_floor_margin = serializers.SerializerMethodField(read_only=True)
    risk_thresholds = serializers.SerializerMethodField(read_only=True)
    hitl_gates = serializers.SerializerMethodField(read_only=True)
    agency_allowlist = serializers.SerializerMethodField(read_only=True)
    agency_blocklist = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AIAutonomyPolicy
        fields = [
            "id",
            "name",
            "description",
            "version",
            "status",
            "policy_json",
            "autonomy_level",
            "level",
            "kill_switch_active",
            "effective_from",
            "effective_to",
            "scope_json",
            "pricing_floor_margin",
            "risk_thresholds",
            "hitl_gates",
            "agency_allowlist",
            "agency_blocklist",
            "created_by",
            "created_by_username",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by_username",
            "approved_by_username",
            "created_at",
            "updated_at",
        ]

    def get_created_by_username(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_approved_by_username(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.username
        return None

    def _pj(self, obj):
        """Return policy_json as a dict, or empty dict."""
        return obj.policy_json if isinstance(obj.policy_json, dict) else {}

    def get_pricing_floor_margin(self, obj):
        return self._pj(obj).get("pricing_floor_margin")

    def get_risk_thresholds(self, obj):
        return self._pj(obj).get("risk_thresholds")

    def get_hitl_gates(self, obj):
        return self._pj(obj).get("hitl_gates")

    def get_agency_allowlist(self, obj):
        pj = self._pj(obj)
        return pj.get("agency_allowlist") or obj.scope_json.get("agency_allowlist") if isinstance(obj.scope_json, dict) else pj.get("agency_allowlist")

    def get_agency_blocklist(self, obj):
        pj = self._pj(obj)
        return pj.get("agency_blocklist") or obj.scope_json.get("agency_blocklist") if isinstance(obj.scope_json, dict) else pj.get("agency_blocklist")

    def validate(self, attrs):
        effective_from = attrs.get("effective_from")
        effective_to = attrs.get("effective_to")
        if effective_from and effective_to and effective_to < effective_from:
            raise serializers.ValidationError(
                {"effective_to": "effective_to must be on or after effective_from."}
            )
        return attrs


class PolicyApprovalSerializer(serializers.ModelSerializer):
    """Serializer for policy approval workflow records."""

    approver_username = serializers.SerializerMethodField(read_only=True)
    policy_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PolicyApproval
        fields = [
            "id",
            "policy",
            "policy_name",
            "approver",
            "approver_username",
            "decision",
            "comments",
            "decided_at",
        ]
        read_only_fields = [
            "id",
            "policy_name",
            "approver_username",
            "decided_at",
        ]

    def get_approver_username(self, obj):
        if obj.approver:
            return obj.approver.get_full_name() or obj.approver.username
        return None

    def get_policy_name(self, obj):
        return str(obj.policy) if obj.policy_id else None


class PolicyEnforcementLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for immutable enforcement log entries."""

    user_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PolicyEnforcementLog
        fields = [
            "id",
            "policy",
            "action_name",
            "deal_id",
            "decision",
            "autonomy_level",
            "risk_score",
            "reason",
            "agent_name",
            "user",
            "user_username",
            "timestamp",
        ]
        read_only_fields = [
            "id",
            "user_username",
            "timestamp",
        ]

    def get_user_username(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None


class AIIncidentSerializer(serializers.ModelSerializer):
    """Full serializer for AI incident records."""

    reported_by_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AIIncident
        fields = [
            "id",
            "title",
            "description",
            "incident_type",
            "severity",
            "status",
            "deal_id",
            "agent_name",
            "freeze_autonomy",
            "reported_by",
            "reported_by_username",
            "resolved_at",
            "resolution_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reported_by_username",
            "created_at",
            "updated_at",
        ]

    def get_reported_by_username(self, obj):
        if obj.reported_by:
            return obj.reported_by.get_full_name() or obj.reported_by.username
        return None
