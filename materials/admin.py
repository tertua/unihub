from django.contrib import admin

from .models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "owner", "created_at")
    list_filter = ("course", "created_at")
    search_fields = ("title", "description", "course")
    raw_id_fields = ("owner",)
