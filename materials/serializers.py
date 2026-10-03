from rest_framework import serializers

from .models import Material

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = (
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
)
ALLOWED_CONTENT_TYPES = (
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/jpeg", "image/png", "image/gif", "image/webp",
)


class MaterialSerializer(serializers.ModelSerializer):
    """Material metadata + file; validation lives here, views stay thin."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Material
        fields = (
            "id", "title", "description", "course",
            "file", "owner", "created_at", "updated_at",
        )
        read_only_fields = ("id", "owner", "created_at", "updated_at")

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title must not be blank.")
        return value

    def validate_file(self, value):
        name = value.name.lower()
        if not name.endswith(ALLOWED_EXTENSIONS):
            raise serializers.ValidationError(
                "Unsupported file type. Allowed: pdf, doc/docx, ppt/pptx, images."
            )
        content_type = getattr(value, "content_type", "")
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError("Unsupported file content type.")
        if value.size > MAX_UPLOAD_SIZE_BYTES:
            raise serializers.ValidationError("File exceeds the 20 MB limit.")
        return value

    def create(self, validated_data):
        # Owner is always the requester, never client-supplied.
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
