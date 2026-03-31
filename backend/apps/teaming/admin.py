from django.contrib import admin

from apps.teaming.models import TeamingPartnership, TeamingPartner, TeamingAgreement


@admin.register(TeamingPartnership)
class TeamingPartnershipAdmin(admin.ModelAdmin):
    list_display = ["partner_company", "deal", "relationship_type", "status", "percentage_of_work", "created_at"]
    list_filter = ["relationship_type", "status", "signed_agreement"]
    search_fields = ["partner_company", "description"]


@admin.register(TeamingPartner)
class TeamingPartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "uei", "clearance_level", "reliability_score", "risk_level", "is_small_business", "is_active"]
    list_filter = ["clearance_level", "risk_level", "is_small_business", "is_active", "is_channel_partner"]
    search_fields = ["name", "uei", "cage_code", "capabilities"]


@admin.register(TeamingAgreement)
class TeamingAgreementAdmin(admin.ModelAdmin):
    list_display = ["partnership", "agreement_type", "status", "signed_date", "expiry_date"]
    list_filter = ["agreement_type", "status"]
    search_fields = ["title", "work_scope"]
