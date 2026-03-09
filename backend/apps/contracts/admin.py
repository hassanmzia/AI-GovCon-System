from django.contrib import admin

from apps.contracts.models import (
    Contract,
    ContractClause,
    ContractTemplate,
    ContractVersion,
)


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "template_type", "is_active", "created_at"]
    list_filter = ["template_type", "is_active"]
    search_fields = ["name"]


@admin.register(ContractClause)
class ContractClauseAdmin(admin.ModelAdmin):
    list_display = [
        "clause_number",
        "title",
        "source",
        "risk_level",
        "is_mandatory",
    ]
    list_filter = ["source", "risk_level", "is_mandatory"]
    search_fields = ["clause_number", "title", "full_text"]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "deal",
        "contract_number",
        "contract_type",
        "status",
        "total_value",
        "period_of_performance_start",
        "period_of_performance_end",
    ]
    list_filter = ["status", "contract_type"]
    search_fields = ["title", "contract_number", "deal__title"]


@admin.register(ContractVersion)
class ContractVersionAdmin(admin.ModelAdmin):
    list_display = [
        "contract",
        "version_number",
        "changed_by",
        "change_summary",
        "created_at",
    ]
    list_filter = ["contract"]
    search_fields = ["contract__title", "change_summary"]
