from django.contrib import admin

from .models import PastPerformance, PastPerformanceMatch


@admin.register(PastPerformance)
class PastPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        "project_name",
        "client_agency",
        "contract_number",
        "contract_type",
        "contract_value",
        "performance_rating",
        "cpars_rating",
        "start_date",
        "end_date",
        "on_time_delivery",
        "within_budget",
        "is_active",
    ]
    list_filter = [
        "is_active",
        "contract_type",
        "performance_rating",
        "cpars_rating",
        "on_time_delivery",
        "within_budget",
    ]
    search_fields = [
        "project_name",
        "client_agency",
        "contract_number",
        "description",
        "client_name",
    ]
    readonly_fields = ["description_embedding"]
    date_hierarchy = "end_date"


@admin.register(PastPerformanceMatch)
class PastPerformanceMatchAdmin(admin.ModelAdmin):
    list_display = [
        "opportunity",
        "past_performance",
        "relevance_score",
        "created_at",
    ]
    list_filter = ["relevance_score"]
    search_fields = [
        "opportunity__title",
        "past_performance__project_name",
        "match_rationale",
    ]
    readonly_fields = ["matched_keywords"]
