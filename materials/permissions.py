from rest_framework import permissions

from accounts.models import User


class IsLecturerOrAdmin(permissions.BasePermission):
    """Write access is limited to lecturers and admins; students read only."""

    message = "Only lecturers and admins may modify materials."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in {User.Role.LECTURER, User.Role.ADMIN}
        )
