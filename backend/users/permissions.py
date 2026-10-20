from rest_framework.permissions import BasePermission

from users.models import RolePermission


class HasPermission(BasePermission):
    """
    Checks whether the authenticated user has the required permission.

    Usage:
        permission_classes = [IsAuthenticated, HasPermission]
        required_permission = "users.view"
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_permission = getattr(
            view,
            "required_permission",
            None
        )

        if not required_permission:
            return False

        return RolePermission.objects.filter(
            role__user_roles__user=request.user,
            permission__codename=required_permission,
        ).exists()