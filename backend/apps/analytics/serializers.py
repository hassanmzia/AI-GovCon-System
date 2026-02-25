from rest_framework import serializers
from apps.analytics.models import AgentPerformanceMetric, DealVelocityMetric, KPISnapshot, WinLossAnalysis


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
