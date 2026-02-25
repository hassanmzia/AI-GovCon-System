from django.contrib import admin

from apps.research.models import (
    CompetitorProfile,
    MarketIntelligence,
    ResearchProject,
    ResearchSource,
)


class ResearchSourceInline(admin.TabularInline):
    model = ResearchSource
    extra = 0
    fields = ["title", "url", "source_type", "relevance_score", "fetched_at"]
    readonly_fields = ["fetched_at"]
    ordering = ["-relevance_score"]


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "deal",
        "status",
        "research_type",
        "requested_by",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "research_type"]
    search_fields = [
        "title",
        "description",
        "executive_summary",
        "deal__title",
    ]
    readonly_fields = ["id", "ai_agent_trace_id", "created_at", "updated_at"]
    raw_id_fields = ["deal", "requested_by"]
    date_hierarchy = "created_at"
    inlines = [ResearchSourceInline]


@admin.register(ResearchSource)
class ResearchSourceAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "project",
        "source_type",
        "relevance_score",
        "fetched_at",
        "created_at",
    ]
    list_filter = ["source_type"]
    search_fields = ["title", "url", "content", "project__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["project"]


@admin.register(CompetitorProfile)
class CompetitorProfileAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "cage_code",
        "duns_number",
        "revenue_range",
        "employee_count",
        "win_rate",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["name", "cage_code", "duns_number", "website"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(MarketIntelligence)
class MarketIntelligenceAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "published_date",
        "relevance_window_days",
        "source_url",
        "created_at",
    ]
    list_filter = ["category", "published_date"]
    search_fields = ["title", "summary", "impact_assessment"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "created_at"
