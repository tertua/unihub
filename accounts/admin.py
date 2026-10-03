from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Full user management from the Django admin, including roles and NIM/NIP."""

    list_display = (
        "username",
        "email",
        "role",
        "student_id_number",
        "lecturer_id_number",
        "study_program",
        "is_staff",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "student_id_number",
        "lecturer_id_number",
    )
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Hub profile",
            {
                "fields": (
                    "role",
                    "student_id_number",
                    "lecturer_id_number",
                    "study_program",
                )
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Hub profile",
            {
                "fields": (
                    "role",
                    "student_id_number",
                    "lecturer_id_number",
                    "study_program",
                )
            },
        ),
    )
