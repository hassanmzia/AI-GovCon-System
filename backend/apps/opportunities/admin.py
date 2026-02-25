from django.contrib import admin

from .models import (
    CompanyProfile,
    DailyDigest,
    Opportunity,
    OpportunityScore,
    OpportunitySource,
)


@admin.register(OpportunitySource)
class OpportunitySourceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "source_type",
        "is_active",
        "scan_frequency_hours",
        "last_scan_at",
        "last_scan_status",
    ]
    list_filter = ["source_type", "is_active", "last_scan_status"]
    search_fields = ["name"]


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = [
        "notice_id",
        "title_short",
        "agency",
        "naics_code",
        "status",
        "posted_date",
        "response_deadline",
        "estimated_value",
        "set_aside",
    ]
    list_filter = [
        "status",
        "is_active",
        "notice_type",
        "set_aside",
        "source",
    ]
    search_fields = [
        "notice_id",
        "title",
        "agency",
        "description",
        "sol_number",
    ]
    readonly_fields = ["raw_data", "description_embedding"]
    date_hierarchy = "posted_date"

    @admin.display(description="Title")
    def title_short(self, obj):
        return obj.title[:80] if obj.title else ""


@admin.register(OpportunityScore)
class OpportunityScoreAdmin(admin.ModelAdmin):
    list_display = [
        "opportunity",
        "total_score",
        "recommendation",
        "naics_match",
        "keyword_overlap",
        "capability_similarity",
        "scored_at",
    ]
    list_filter = ["recommendation"]
    search_fields = ["opportunity__notice_id", "opportunity__title"]
    readonly_fields = ["score_explanation"]


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "uei_number",
        "cage_code",
        "is_primary",
        "created_at",
    ]
    list_filter = ["is_primary"]
    search_fields = ["name", "uei_number", "cage_code"]
    readonly_fields = ["capability_embedding"]


@admin.register(DailyDigest)
class DailyDigestAdmin(admin.ModelAdmin):
    list_display = [
        "date",
        "total_scanned",
        "total_new",
        "total_scored",
        "is_sent",
    ]
    list_filter = ["is_sent"]
    date_hierarchy = "date"
    filter_horizontal = ["opportunities"]
