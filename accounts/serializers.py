from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """Public self-registration. Password is hashed in create(), never returned."""

    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "password",
            "role",
            "student_id_number",
            "study_program",
        )
        read_only_fields = ("id",)

    def validate_role(self, value):
        # Admins are provisioned through /admin/, never self-registered.
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Admin accounts cannot self-register.")
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MeSerializer(serializers.ModelSerializer):
    """Own profile: identity fields are read-only so the academic mapping
    (NIM/NIP, see docs/adr/002) stays under admin control."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "role",
            "first_name",
            "last_name",
            "email",
            "student_id_number",
            "lecturer_id_number",
            "study_program",
        )
        read_only_fields = (
            "id",
            "username",
            "role",
            "student_id_number",
            "lecturer_id_number",
        )
