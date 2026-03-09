from django.contrib import admin

from apps.sba_certifications.models import NAICSCode, SBACertification


@admin.register(SBACertification)
class SBACertificationAdmin(admin.ModelAdmin):
    list_display = ["cert_type", "status", "certification_number", "expiration_date", "owner"]
    list_filter = ["cert_type", "status"]
    search_fields = ["certification_number", "owner__email"]


@admin.register(NAICSCode)
class NAICSCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "is_primary", "qualifies_small", "owner"]
    list_filter = ["is_primary", "qualifies_small"]
    search_fields = ["code", "title"]
