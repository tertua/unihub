import logging

from rest_framework import serializers

from . import drive
from .models import Material

logger = logging.getLogger(__name__)

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

DRIVE_HOST_ALLOWLIST = ("drive.google.com", "docs.google.com")


class MaterialSerializer(serializers.ModelSerializer):
    """Material metadata + file or Drive link; validation lives here, views stay thin."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    file = serializers.FileField(required=False, allow_null=True)
    source_url = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=500
    )
    drive_file_id = serializers.CharField(read_only=True)
    source_type = serializers.SerializerMethodField()
    embed_url = serializers.SerializerMethodField()
    drive_name = serializers.SerializerMethodField()
    drive_mime_type = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = (
            "id", "title", "description", "course",
            "file", "source_url", "drive_file_id", "source_type",
            "embed_url", "drive_name", "drive_mime_type",
            "owner", "created_at", "updated_at",
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

    def validate_source_url(self, value):
        # A single message covers both "wrong host" and "no Drive ID" so the
        # response cannot be used to probe which check failed.
        if value in (None, ""):
            return value
        ref = drive.parse_drive_url(value.strip())
        if ref is None:
            raise serializers.ValidationError(
                "Enter a Google Drive link from drive.google.com or docs.google.com."
            )
        return drive.canonical_url(ref)

    def validate(self, attrs):
        # Evaluate the post-update state so PATCH/PUT cannot leave both set or both empty.
        has_file = bool(attrs.get("file", getattr(self.instance, "file", None)))
        has_url = bool(attrs.get("source_url", getattr(self.instance, "source_url", None)))
        if has_file and has_url:
            raise serializers.ValidationError(
                {"source_url": "Provide either a file or a Drive link, not both."}
            )
        if not has_file and not has_url:
            # Keyed under both fields so the honest "a source is required"
            # error is discoverable whichever field the client inspects.
            raise serializers.ValidationError(
                {
                    "file": "Provide a file or a Drive link.",
                    "source_url": "Provide a file or a Drive link.",
                }
            )
        return attrs

    def create(self, validated_data):
        # Owner is always the requester, never client-supplied.
        validated_data["owner"] = self.context["request"].user
        source_url = validated_data.get("source_url")
        validated_data["drive_file_id"] = (
            drive.parse_drive_url(source_url).file_id if source_url else ""
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Keep the stored identity in sync with any new link.
        if "source_url" in validated_data:
            source_url = validated_data["source_url"]
            validated_data["drive_file_id"] = (
                drive.parse_drive_url(source_url).file_id if source_url else ""
            )
        new_file = validated_data.get("file")
        old_file = instance.file
        updated = super().update(instance, validated_data)
        # Replace (not orphan) the previous object. Deleting after the save means
        # a failed save cannot destroy the old upload, and a storage hiccup must
        # not turn a successful PATCH into a 500.
        if new_file and old_file and old_file.name != new_file.name:
            try:
                old_file.storage.delete(old_file.name)
            except Exception:
                logger.warning(
                    "Could not delete replaced file %s; left as-is.", old_file.name
                )
        return updated

    def get_source_type(self, obj):
        return "file" if obj.file else "link"

    def _ref(self, obj):
        if not obj.source_url:
            return None
        return drive.parse_drive_url(obj.source_url)

    def get_embed_url(self, obj):
        # Link materials: derive from source_url.
        ref = self._ref(obj)
        if ref is not None:
            return drive.embed_url(ref)
        # File materials on Drive storage: the stored name is the Drive id.
        if obj.file:
            stored = obj.file.name
            if drive.is_drive_file_id(stored):
                return drive.file_embed_url(stored)
        return None

    def get_drive_name(self, obj):
        meta = self._metadata(obj)
        return meta["name"] if meta else None

    def get_drive_mime_type(self, obj):
        meta = self._metadata(obj)
        return meta["mime_type"] if meta else None

    def _metadata(self, obj):
        """Resolve Drive metadata once per object; both drive_* fields read here.

        Memoised on the instance for the duration of one `to_representation`, so
        a list page pays at most one (cache-backed) lookup per row instead of two.
        """
        fid = self._metadata_file_id(obj)
        if not fid:
            return None
        if not hasattr(obj, "_drive_metadata"):
            obj._drive_metadata = drive.fetch_metadata(fid)
        return obj._drive_metadata

    @staticmethod
    def _file_drive_id(obj):
        # Reuse the FileField stored name; no extra column (P14).
        if obj.file and drive.is_drive_file_id(obj.file.name):
            return obj.file.name
        return ""

    def _metadata_file_id(self, obj):
        return obj.drive_file_id or self._file_drive_id(obj)


class DriveBrowseEntrySerializer(serializers.Serializer):
    """One child of a Drive folder as returned by the browse endpoint."""

    id = serializers.CharField()
    name = serializers.CharField()
    mimeType = serializers.CharField()
    isFolder = serializers.BooleanField()
    url = serializers.URLField(allow_blank=True)


class DriveBrowseResponseSerializer(serializers.Serializer):
    """Response envelope for GET /api/v1/drive/."""

    configured = serializers.BooleanField()
    parent = serializers.CharField(allow_null=True, allow_blank=True)
    results = DriveBrowseEntrySerializer(many=True)
    truncated = serializers.BooleanField()
