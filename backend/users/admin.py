from django.contrib import admin

from .models import (
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
    AuditLog,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "is_active",
        "is_staff",
        "created_at",
    )
    search_fields = (
        "email",
        "full_name",
    )
    list_filter = (
        "is_active",
        "is_staff",
    )
    readonly_fields = (
        "id",
        "created_at",
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "is_system",
        "created_at",
    )
    search_fields = (
        "name",
        "description",
    )
    list_filter = (
        "is_system",
    )
    readonly_fields = (
        "id",
        "created_at",
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        "codename",
        "description",
    )
    search_fields = (
        "codename",
        "description",
    )
    readonly_fields = (
        "id",
    )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "assigned_at",
    )
    search_fields = (
        "user__email",
        "user__full_name",
        "role__name",
    )
    list_filter = (
        "role",
    )
    readonly_fields = (
        "id",
        "assigned_at",
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = (
        "role",
        "permission",
    )
    search_fields = (
        "role__name",
        "permission__codename",
    )
    list_filter = (
        "role",
        "permission",
    )
    readonly_fields = (
        "id",
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "actor",
        "target_type",
        "target_id",
        "ip_address",
        "created_at",
    )
    search_fields = (
        "action",
        "target_type",
        "target_id",
        "actor__email",
        "actor__full_name",
    )
    list_filter = (
        "action",
        "target_type",
        "created_at",
    )
    readonly_fields = (
        "id",
        "actor",
        "action",
        "target_type",
        "target_id",
        "ip_address",
        "metadata",
        "created_at",
    )