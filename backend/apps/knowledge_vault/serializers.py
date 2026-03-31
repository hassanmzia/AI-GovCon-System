from rest_framework import serializers

from apps.knowledge_vault.models import DocumentTemplate, KnowledgeDocument


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    reviewer_username = serializers.CharField(source="reviewer.username", read_only=True)

    class Meta:
        model = KnowledgeDocument
        fields = [
            "id",
            "title",
            "description",
            "category",
            "content",
            "file_url",
            "file_name",
            "status",
            "tags",
            "keywords",
            "author",
            "author_username",
            "reviewer",
            "reviewer_username",
            "reviewed_at",
            "version",
            "related_documents",
            "is_public",
            "downloads",
            "views",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "downloads", "views", "created_at", "updated_at"]


class DocumentTemplateListSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name", read_only=True, default=""
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentTemplate
        fields = [
            "id",
            "name",
            "description",
            "category",
            "file_format",
            "file_size",
            "version",
            "source",
            "tags",
            "is_active",
            "is_default",
            "usage_count",
            "uploaded_by",
            "uploaded_by_name",
            "file_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "file_size",
            "usage_count",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj):
        """Return a URL to the Django-served download endpoint.

        Instead of linking directly to MinIO/S3 (which may 404 for seeded
        templates), we route through the /templates/{id}/download/ action
        which has a local-file fallback.
        """
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(
                    f"/api/knowledge-vault/templates/{obj.id}/download/"
                )
            return f"/api/knowledge-vault/templates/{obj.id}/download/"
        return None


class DocumentTemplateDetailSerializer(DocumentTemplateListSerializer):
    variables = serializers.JSONField(required=False, default=list)

    class Meta(DocumentTemplateListSerializer.Meta):
        fields = DocumentTemplateListSerializer.Meta.fields + ["variables", "file"]

    def validate_file(self, value):
        if value:
            max_size = 50 * 1024 * 1024  # 50 MB
            if value.size > max_size:
                raise serializers.ValidationError("File size must be under 50 MB.")
        return value
