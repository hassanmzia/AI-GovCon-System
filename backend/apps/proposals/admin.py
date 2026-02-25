from django.contrib import admin

from .models import (
    Proposal,
    ProposalSection,
    ProposalTemplate,
    ReviewComment,
    ReviewCycle,
)


@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "is_default",
        "created_at",
    ]
    list_filter = ["is_default"]
    search_fields = ["name", "description"]


class ProposalSectionInline(admin.TabularInline):
    model = ProposalSection
    extra = 0
    fields = [
        "volume",
        "section_number",
        "title",
        "order",
        "status",
        "assigned_to",
        "word_count",
        "page_limit",
    ]


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "deal",
        "version",
        "status",
        "compliance_percentage",
        "total_requirements",
        "compliant_count",
        "created_at",
    ]
    list_filter = ["status", "version"]
    search_fields = ["title", "executive_summary", "deal__title"]
    inlines = [ProposalSectionInline]


@admin.register(ProposalSection)
class ProposalSectionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "proposal",
        "volume",
        "section_number",
        "order",
        "status",
        "assigned_to",
        "word_count",
        "page_limit",
    ]
    list_filter = ["status", "volume"]
    search_fields = ["title", "section_number", "proposal__title"]


class ReviewCommentInline(admin.TabularInline):
    model = ReviewComment
    extra = 0
    fields = [
        "section",
        "reviewer",
        "comment_type",
        "content",
        "is_resolved",
    ]


@admin.register(ReviewCycle)
class ReviewCycleAdmin(admin.ModelAdmin):
    list_display = [
        "proposal",
        "review_type",
        "status",
        "scheduled_date",
        "completed_date",
        "overall_score",
    ]
    list_filter = ["review_type", "status"]
    search_fields = ["proposal__title", "summary"]
    filter_horizontal = ["reviewers"]
    inlines = [ReviewCommentInline]


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = [
        "review",
        "section",
        "reviewer",
        "comment_type",
        "is_resolved",
        "created_at",
    ]
    list_filter = ["comment_type", "is_resolved"]
    search_fields = ["content", "section__title", "review__proposal__title"]
