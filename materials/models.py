from django.conf import settings
from django.db import models


class Material(models.Model):
    """A course document — an uploaded file OR a Google Drive link (Material Hub)."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    course = models.CharField(max_length=128, blank=True, db_index=True)
    # FileField, not ImageField: Pillow is intentionally not a dependency.
    file = models.FileField(upload_to="materials/%Y/%m/", blank=True, null=True)
    # Drive link materials. `source_url` holds the canonical URL, `drive_file_id`
    # the extracted identity; the XOR with `file` is enforced in the serializer.
    source_url = models.URLField(max_length=500, blank=True, null=True)
    drive_file_id = models.CharField(max_length=128, blank=True, default="")
    # PROTECT: deleting an account must never silently orphan hub materials.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="materials",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = (
            models.CheckConstraint(
                name="material_exactly_one_source",
                # Exactly one of file / source_url present and non-empty; the
                # `__isnull=True | =''` pair covers the admin's empty-string file.
                condition=(
                    (models.Q(file__isnull=True) | models.Q(file=""))
                    ^ (models.Q(source_url__isnull=True) | models.Q(source_url=""))
                ),
            ),
        )

    def __str__(self):
        return self.title
