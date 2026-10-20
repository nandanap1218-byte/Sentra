
from rest_framework import serializers

from users.models import (
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
    AuditLog,
)


# ============================================================
# REGISTER SERIALIZER
# Public registration still requires a password.
# ============================================================

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "password",
        ]
        read_only_fields = [
            "id",
        ]

    def validate_email(self, value):
        return value.strip().lower()

    def validate_full_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Full name cannot be empty."
            )

        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


# ============================================================
# USER CREATE SERIALIZER
# Admin creates a user using only full_name and email.
# No password is required or accepted.
# ============================================================

class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
        ]
        read_only_fields = [
            "id",
        ]

    def validate_email(self, value):
        return value.strip().lower()

    def validate_full_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Full name cannot be empty."
            )

        return value

    def create(self, validated_data):
        user = User(**validated_data)

        # No default or temporary password is created.
        # The account cannot log in using a password
        # until a password-setting process is implemented.
        user.set_unusable_password()

        user.save()

        return user


# ============================================================
# USER UPDATE SERIALIZER
# ============================================================

class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "is_active",
        ]

    def validate_email(self, value):
        return value.strip().lower()

    def validate_full_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Full name cannot be empty."
            )

        return value


# ============================================================
# USER DETAIL SERIALIZER
# ============================================================

class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "is_active",
            "is_staff",
            "created_at",
            "last_login",
        ]

        read_only_fields = [
            "id",
            "is_staff",
            "created_at",
            "last_login",
        ]


# ============================================================
# ROLE SERIALIZER
# ============================================================

class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "is_system",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "is_system",
            "created_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Role name cannot be empty."
            )

        return value


# ============================================================
# USER ROLE SERIALIZER
# ============================================================

class UserRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserRole
        fields = [
            "id",
            "user",
            "role",
            "assigned_at",
        ]

        read_only_fields = [
            "id",
            "assigned_at",
        ]


# ============================================================
# USER ROLE DETAIL SERIALIZER
# ============================================================

class UserRoleDetailSerializer(serializers.ModelSerializer):

    role_name = serializers.CharField(
        source="role.name",
        read_only=True
    )

    role_description = serializers.CharField(
        source="role.description",
        read_only=True
    )

    class Meta:
        model = UserRole
        fields = [
            "id",
            "role",
            "role_name",
            "role_description",
            "assigned_at",
        ]

        read_only_fields = [
            "id",
            "role",
            "role_name",
            "role_description",
            "assigned_at",
        ]


# ============================================================
# PERMISSION SERIALIZER
# ============================================================

class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = [
            "id",
            "codename",
            "description",
        ]

        read_only_fields = [
            "id",
        ]

    def validate_codename(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Permission codename cannot be empty."
            )

        return value


# ============================================================
# ROLE PERMISSION SERIALIZER
# ============================================================

class RolePermissionSerializer(serializers.ModelSerializer):

    permission_name = serializers.CharField(
        source="permission.codename",
        read_only=True
    )

    permission_description = serializers.CharField(
        source="permission.description",
        read_only=True
    )

    class Meta:
        model = RolePermission
        fields = [
            "id",
            "role",
            "permission",
            "permission_name",
            "permission_description",
        ]

        read_only_fields = [
            "id",
            "permission_name",
            "permission_description",
        ]


# ============================================================
# AUDIT LOG SERIALIZER
# ============================================================

class AuditLogSerializer(serializers.ModelSerializer):

    actor_email = serializers.CharField(
        source="actor.email",
        read_only=True
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_email",
            "action",
            "target_type",
            "target_id",
            "ip_address",
            "metadata",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "actor",
            "actor_email",
            "created_at",
        ]
