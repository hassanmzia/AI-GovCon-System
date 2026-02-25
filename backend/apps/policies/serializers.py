from rest_framework import serializers
from .models import BusinessPolicy, PolicyRule, PolicyEvaluation, PolicyException


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
