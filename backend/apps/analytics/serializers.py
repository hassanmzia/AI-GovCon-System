from rest_framework import serializers
from apps.analytics.models import (
    AIAgentRun,
    AgentPerformanceMetric,
    DealVelocityMetric,
    KPISnapshot,
    RecommendationMetric,
    RevenueForecast,
    WinLossAnalysis,
)


class KPISnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPISnapshot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class DealVelocityMetricSerializer(serializers.ModelSerializer):
    deal_title = serializers.CharField(source="deal.title", read_only=True)

    class Meta:
        model = DealVelocityMetric
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class WinLossAnalysisSerializer(serializers.ModelSerializer):
    deal_title = serializers.CharField(source="deal.title", read_only=True)
    deal_stage = serializers.CharField(source="deal.stage", read_only=True)

    class Meta:
        model = WinLossAnalysis
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AgentPerformanceMetricSerializer(serializers.ModelSerializer):
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = AgentPerformanceMetric
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_success_rate(self, obj):
        if obj.total_runs == 0:
            return None
        return round((obj.successful_runs / obj.total_runs) * 100, 1)


class RecommendationMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationMetric
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class RevenueForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueForecast
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AIAgentRunSerializer(serializers.ModelSerializer):
    """Serializer for individual AI agent execution records."""

    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = AIAgentRun
        fields = [
            "id",
            "agent_name",
            "deal_id",
            "action",
            "status",
            "started_at",
            "completed_at",
            "duration_seconds",
            "latency_ms",
            "cost_usd",
            "input_tokens",
            "output_tokens",
            "success",
            "confidence",
            "hallucination_flags",
            "citations_present",
            "human_edit_delta",
            "override",
            "risk_score",
            "autonomy_level",
            "error_message",
            "user",
        ]
        read_only_fields = ["id", "started_at"]

    def get_duration_seconds(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return round(delta.total_seconds(), 2)
        return None
