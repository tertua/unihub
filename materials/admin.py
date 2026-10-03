from django.contrib import admin

from .models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "source_kind", "owner", "created_at")
    list_filter = ("course", "created_at")
    search_fields = ("title", "description", "course", "source_url")
    raw_id_fields = ("owner",)

    @admin.display(description="Source")
    def source_kind(self, obj):
        return "file" if obj.file else "drive link"
