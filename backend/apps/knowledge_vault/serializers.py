from rest_framework import serializers

from apps.knowledge_vault.models import KnowledgeDocument


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
