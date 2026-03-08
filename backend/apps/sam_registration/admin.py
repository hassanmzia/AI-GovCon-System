from django.contrib import admin

from apps.sam_registration.models import SAMContact, SAMRegistration


class SAMContactInline(admin.TabularInline):
    model = SAMContact
    extra = 0


@admin.register(SAMRegistration)
class SAMRegistrationAdmin(admin.ModelAdmin):
    list_display = ["legal_business_name", "uei_number", "status", "expiration_date", "owner"]
    list_filter = ["status"]
    search_fields = ["legal_business_name", "uei_number", "cage_code"]
    inlines = [SAMContactInline]


@admin.register(SAMContact)
class SAMContactAdmin(admin.ModelAdmin):
    list_display = ["name", "role", "email", "registration"]
    list_filter = ["role"]
