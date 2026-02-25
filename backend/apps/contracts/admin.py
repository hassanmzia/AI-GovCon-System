from django.contrib import admin

from apps.contracts.models import (
    Contract,
    ContractClause,
    ContractTemplate,
    ContractVersion,
)


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "contract_type", "is_active", "created_at"]
    list_filter = ["contract_type", "is_active"]
    search_fields = ["name"]


@admin.register(ContractClause)
class ContractClauseAdmin(admin.ModelAdmin):
    list_display = [
        "clause_number",
        "title",
        "clause_type",
        "risk_level",
        "is_negotiable",
    ]
    list_filter = ["clause_type", "risk_level", "is_negotiable"]
    search_fields = ["clause_number", "title", "clause_text"]


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
        "created_by",
        "description",
        "created_at",
    ]
    list_filter = ["contract"]
    search_fields = ["contract__title", "description"]
