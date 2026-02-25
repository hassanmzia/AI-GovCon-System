from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_mfa_enabled",
        "is_active",
        "is_staff",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "is_mfa_enabled"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    inlines = [UserProfileInline]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("role", "is_mfa_enabled")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Custom Fields", {"fields": ("email", "role")}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "department", "phone"]
    search_fields = [
        "user__username",
        "user__email",
        "title",
        "department",
    ]
    list_filter = ["department"]
    raw_id_fields = ["user"]
