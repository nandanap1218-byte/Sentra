
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from users.models import (
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
    AuditLog,
)

from users.serializers import (
    RegisterSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserDetailSerializer,
    RoleSerializer,
    PermissionSerializer,
    UserRoleDetailSerializer,
    AuditLogSerializer,
)

from users.permissions import HasPermission


# ============================================================
# PERMISSION HELPER
# ============================================================

def has_permission(request, permission_code):
    checker = HasPermission()

    return checker.has_permission(
        request,
        type(
            "RequiredPermissionView",
            (),
            {"required_permission": permission_code},
        ),
    )


# ============================================================
# AUDIT LOG HELPER
# ============================================================

def create_audit_log(
    request,
    action,
    target_type,
    target_id=None,
    metadata=None,
):
    actor = (
        request.user
        if request.user and request.user.is_authenticated
        else None
    )

    ip_address = request.META.get("HTTP_X_FORWARDED_FOR")

    if ip_address:
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR")

    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        ip_address=ip_address,
        metadata=metadata or {},
    )


# ============================================================
# PERMISSION LOOKUP HELPER
# Supports permission UUIDs and codenames.
# ============================================================

def get_permission_by_identifier(identifier):
    if not isinstance(identifier, (str, UUID)):
        return None

    identifier = str(identifier).strip()

    if not identifier:
        return None

    permission = Permission.objects.filter(
        codename=identifier
    ).first()

    if permission:
        return permission

    try:
        permission_uuid = UUID(identifier)
    except (ValueError, TypeError, AttributeError):
        return None

    return Permission.objects.filter(id=permission_uuid).first()


# ============================================================
# REGISTER
# POST /api/auth/register/
# ============================================================

class RegisterView(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()

        create_audit_log(
            request=request,
            action="user.register",
            target_type="User",
            target_id=user.id,
            metadata={
                "email": user.email,
                "full_name": user.full_name,
            },
        )

        return Response(
            {
                "message": "User registered successfully.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# LOGIN
# POST /api/auth/login/
# ============================================================

class LoginView(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "User account is inactive."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)

        create_audit_log(
            request=request,
            action="user.login",
            target_type="User",
            target_id=user.id,
            metadata={"email": user.email},
        )

        response = Response(
            {
                "message": "Login successful.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "last_login": user.last_login,
                },
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key=settings.REFRESH_COOKIE_NAME,
            value=str(refresh),
            max_age=settings.REFRESH_COOKIE_MAX_AGE,
            httponly=settings.REFRESH_COOKIE_HTTP_ONLY,
            secure=settings.REFRESH_COOKIE_SECURE,
            samesite=settings.REFRESH_COOKIE_SAMESITE,
        )

        return response


# ============================================================
# REFRESH TOKEN
# POST /api/auth/refresh/
# ============================================================

class RefreshView(APIView):

    permission_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.REFRESH_COOKIE_NAME
        )

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            old_refresh = RefreshToken(refresh_token)
            user_id = old_refresh.get("user_id")
            user = User.objects.get(id=user_id)

            if not user.is_active:
                return Response(
                    {"detail": "User account is inactive."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            old_refresh.blacklist()
            new_refresh = RefreshToken.for_user(user)

            response = Response(
                {"access": str(new_refresh.access_token)},
                status=status.HTTP_200_OK,
            )

            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=str(new_refresh),
                max_age=settings.REFRESH_COOKIE_MAX_AGE,
                httponly=settings.REFRESH_COOKIE_HTTP_ONLY,
                secure=settings.REFRESH_COOKIE_SECURE,
                samesite=settings.REFRESH_COOKIE_SAMESITE,
            )

            return response

        except (TokenError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


# ============================================================
# LOGOUT
# POST /api/auth/logout/
# ============================================================

class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.REFRESH_COOKIE_NAME
        )

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()

                create_audit_log(
                    request=request,
                    action="user.logout",
                    target_type="User",
                    target_id=request.user.id,
                    metadata={"email": request.user.email},
                )
            except TokenError:
                pass

        response = Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie(settings.REFRESH_COOKIE_NAME)
        return response


# ============================================================
# CURRENT USER
# GET /api/auth/me/
# ============================================================

class MeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        user_roles = (
            UserRole.objects
            .filter(user=user)
            .select_related("role")
        )

        roles = []
        permission_codenames = set()

        for user_role in user_roles:
            role = user_role.role

            roles.append({
                "id": str(role.id),
                "name": role.name,
                "description": role.description,
            })

            role_permissions = (
                RolePermission.objects
                .filter(role=role)
                .select_related("permission")
            )

            for role_permission in role_permissions:
                permission_codenames.add(
                    role_permission.permission.codename
                )

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "last_login": user.last_login,
                "roles": roles,
                "permissions": sorted(permission_codenames),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# USER LIST / CREATE
# GET  /api/auth/users/
# POST /api/auth/users/
# ============================================================

class UserListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not has_permission(request, "users.view"):
            return Response(
                {"detail": "You do not have permission to view users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        active_count = User.objects.filter(is_active=True).count()

        users = User.objects.all()
        search = request.query_params.get("search", "").strip()

        if search:
            users = users.filter(
                Q(full_name__icontains=search)
                | Q(email__icontains=search)
            )

        is_active = request.query_params.get("is_active")

        if is_active is not None:
            if is_active.lower() == "true":
                users = users.filter(is_active=True)
            elif is_active.lower() == "false":
                users = users.filter(is_active=False)

        role_id = request.query_params.get("role")

        if role_id:
            users = users.filter(
                user_roles__role_id=role_id
            ).distinct()

        ordering = request.query_params.get(
            "ordering",
            "-created_at",
        )

        allowed_ordering = {
            "full_name", "-full_name",
            "email", "-email",
            "created_at", "-created_at",
            "is_active", "-is_active",
            "last_login", "-last_login",
        }

        if ordering not in allowed_ordering:
            ordering = "-created_at"

        users = users.order_by(ordering)

        try:
            page = int(request.query_params.get("page", 1))
        except (TypeError, ValueError):
            page = 1

        try:
            page_size = int(
                request.query_params.get("page_size", 4)
            )
        except (TypeError, ValueError):
            page_size = 4

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        total_count = users.count()
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = users[start:end]

        results = []

        for user in paginated_users:
            user_roles = (
                UserRole.objects
                .filter(user=user)
                .select_related("role")
                .order_by("role__name")
            )

            roles = [
                {
                    "id": str(item.role.id),
                    "name": item.role.name,
                }
                for item in user_roles
            ]

            results.append({
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "created_at": user.created_at,
                "last_login": user.last_login,
                "roles": roles,
            })

        query_params = request.query_params.copy()

        next_url = None
        previous_url = None

        if end < total_count:
            query_params["page"] = str(page + 1)
            next_url = request.build_absolute_uri(
                "?" + query_params.urlencode()
            )

        if start > 0:
            query_params["page"] = str(page - 1)
            previous_url = request.build_absolute_uri(
                "?" + query_params.urlencode()
            )

        return Response(
            {
                "count": total_count,
                "active_count": active_count,
                "next": next_url,
                "previous": previous_url,
                "results": results,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        if not has_permission(request, "users.create"):
            return Response(
                {"detail": "You do not have permission to create users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Role assignment is handled separately and requires
        # users.roles.assign.
        serializer = UserCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()

        create_audit_log(
            request=request,
            action="user.create",
            target_type="User",
            target_id=user.id,
            metadata={
                "email": user.email,
                "full_name": user.full_name,
            },
        )

        return Response(
            {
                "message": "User created successfully.",
                "user": UserDetailSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# USER DETAIL
# GET    /api/auth/users/<uuid:user_id>/
# PATCH  /api/auth/users/<uuid:user_id>/
# DELETE /api/auth/users/<uuid:user_id>/
# ============================================================

class UserDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return None

    def get(self, request, user_id):
        if not has_permission(request, "users.view"):
            return Response(
                {"detail": "You do not have permission to view users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_user(user_id)

        if user is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            UserDetailSerializer(user).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, user_id):
        if not has_permission(request, "users.edit"):
            return Response(
                {"detail": "You do not have permission to edit users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_user(user_id)

        if user is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        old_data = {
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
        }

        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()

        create_audit_log(
            request=request,
            action="user.update",
            target_type="User",
            target_id=user.id,
            metadata={
                "before": old_data,
                "after": {
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                },
            },
        )

        return Response(
            {
                "message": "User updated successfully.",
                "user": UserDetailSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, user_id):
        # Deactivation requires users.edit.
        if not has_permission(request, "users.edit"):
            return Response(
                {
                    "detail": (
                        "You do not have permission to deactivate users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_user(user_id)

        if user is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.id == request.user.id:
            return Response(
                {"detail": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = user.email
        was_active = user.is_active

        user.is_active = False
        user.save(update_fields=["is_active"])

        create_audit_log(
            request=request,
            action="user.deactivate",
            target_type="User",
            target_id=user.id,
            metadata={
                "email": email,
                "before": {"is_active": was_active},
                "after": {"is_active": False},
            },
        )

        return Response(
            {"message": "User deactivated successfully."},
            status=status.HTTP_200_OK,
        )


# ============================================================
# ROLE LIST / CREATE
# ============================================================

class RoleListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not has_permission(request, "roles.view"):
            return Response(
                {"detail": "You do not have permission to view roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        roles = Role.objects.all().order_by("name")
        data = []

        for role in roles:
            role_permissions = (
                RolePermission.objects
                .filter(role=role)
                .select_related("permission")
            )

            data.append({
                "id": str(role.id),
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system,
                "permissions": [
                    item.permission.codename
                    for item in role_permissions
                ],
            })

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        if not has_permission(request, "roles.manage"):
            return Response(
                {"detail": "You do not have permission to create roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RoleSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = serializer.save()

        create_audit_log(
            request=request,
            action="role.create",
            target_type="Role",
            target_id=role.id,
            metadata={
                "name": role.name,
                "description": role.description,
            },
        )

        return Response(
            {
                "message": "Role created successfully.",
                "role": RoleSerializer(role).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# ROLE DETAIL
# ============================================================

class RoleDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_role(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except (Role.DoesNotExist, ValueError, TypeError):
            return None

    def get(self, request, role_id):
        if not has_permission(request, "roles.view"):
            return Response(
                {"detail": "You do not have permission to view roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if role is None:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            RoleSerializer(role).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, role_id):
        if not has_permission(request, "roles.manage"):
            return Response(
                {"detail": "You do not have permission to manage roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if role is None:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if role.is_system:
            return Response(
                {"detail": "System roles cannot be modified."},
                status=status.HTTP_403_FORBIDDEN,
            )

        old_data = {
            "name": role.name,
            "description": role.description,
        }

        serializer = RoleSerializer(
            role,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_role = serializer.save()

        create_audit_log(
            request=request,
            action="role.update",
            target_type="Role",
            target_id=updated_role.id,
            metadata={
                "before": old_data,
                "after": {
                    "name": updated_role.name,
                    "description": updated_role.description,
                },
            },
        )

        return Response(
            RoleSerializer(updated_role).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, role_id):
        if not has_permission(request, "roles.manage"):
            return Response(
                {"detail": "You do not have permission to manage roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if role is None:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if role.is_system:
            return Response(
                {"detail": "System roles cannot be deleted."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role_id_str = str(role.id)
        role_name = role.name
        role.delete()

        create_audit_log(
            request=request,
            action="role.delete",
            target_type="Role",
            target_id=role_id_str,
            metadata={"name": role_name},
        )

        return Response(
            {"message": "Role deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ============================================================
# USER ROLE ASSIGNMENT
# GET    /api/auth/users/<uuid:user_id>/roles/
# POST   /api/auth/users/<uuid:user_id>/roles/
# PUT    /api/auth/users/<uuid:user_id>/roles/
#
# GET requires roles.view.
# POST / PUT require users.roles.assign.
# ============================================================

class UserRoleView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if not has_permission(request, "roles.view"):
            return Response(
                {"detail": "You do not have permission to view user roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_roles = (
            UserRole.objects
            .filter(user=user)
            .select_related("role")
        )

        serializer = UserRoleDetailSerializer(
            user_roles,
            many=True,
        )

        return Response(
            {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },
                "roles": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, user_id):
        if not has_permission(request, "users.roles.assign"):
            return Response(
                {"detail": "You do not have permission to assign roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role_id = request.data.get("role_id")

        if not role_id:
            return Response(
                {"detail": "role_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            role = Role.objects.get(id=role_id)
        except (Role.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if UserRole.objects.filter(user=user, role=role).exists():
            return Response(
                {"detail": "Role is already assigned to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_role = UserRole.objects.create(user=user, role=role)

        create_audit_log(
            request=request,
            action="role.assign",
            target_type="UserRole",
            target_id=user_role.id,
            metadata={
                "user_id": str(user.id),
                "user_email": user.email,
                "role_id": str(role.id),
                "role_name": role.name,
            },
        )

        return Response(
            {
                "message": "Role assigned successfully.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                },
                "assignment": {
                    "id": str(user_role.id),
                    "assigned_at": user_role.assigned_at,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    def put(self, request, user_id):
        if not has_permission(request, "users.roles.assign"):
            return Response(
                {"detail": "You do not have permission to manage user roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role_ids = request.data.get("role_ids")

        if role_ids is None:
            return Response(
                {"detail": "role_ids is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(role_ids, list):
            return Response(
                {"detail": "role_ids must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unique_role_ids = list(
            dict.fromkeys(str(role_id) for role_id in role_ids)
        )

        if user.id == request.user.id:
            current_admin = UserRole.objects.filter(
                user=user,
                role__name__iexact="Admin",
            ).exists()

            requested_admin = Role.objects.filter(
                id__in=unique_role_ids,
                name__iexact="Admin",
            ).exists()

            if current_admin and not requested_admin:
                return Response(
                    {"detail": "You cannot remove your own Admin role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        roles = list(Role.objects.filter(id__in=unique_role_ids))
        role_map = {str(role.id): role for role in roles}

        if set(role_map.keys()) != set(unique_role_ids):
            return Response(
                {"detail": "One or more roles were not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        roles = [role_map[role_id] for role_id in unique_role_ids]

        old_user_roles = list(
            UserRole.objects.filter(user=user).select_related("role")
        )

        old_role_data = [
            {"id": str(item.role.id), "name": item.role.name}
            for item in old_user_roles
        ]

        new_role_data = [
            {"id": str(role.id), "name": role.name}
            for role in roles
        ]

        with transaction.atomic():
            UserRole.objects.filter(user=user).delete()

            UserRole.objects.bulk_create([
                UserRole(user=user, role=role)
                for role in roles
            ])

            create_audit_log(
                request=request,
                action="user.roles.update",
                target_type="User",
                target_id=user.id,
                metadata={
                    "before": old_role_data,
                    "after": new_role_data,
                },
            )

        return Response(
            {
                "message": "User roles updated successfully.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },
                "roles": new_role_data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# USER ROLE DETAIL
# DELETE /api/auth/users/<uuid:user_id>/roles/<uuid:role_id>/
# Requires users.roles.assign.
# ============================================================

class UserRoleDetailView(APIView):

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "users.roles.assign"

    def delete(self, request, user_id, role_id):
        try:
            user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            role = Role.objects.get(id=role_id)
        except (Role.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            user_role = UserRole.objects.get(user=user, role=role)
        except UserRole.DoesNotExist:
            return Response(
                {"detail": "Role is not assigned to this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.id == request.user.id and role.name.lower() == "admin":
            other_admins = UserRole.objects.filter(
                role__name__iexact="Admin"
            ).exclude(user=user).exists()

            if not other_admins:
                return Response(
                    {
                        "detail": (
                            "You cannot remove your own Admin role "
                            "when no other Admin exists."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        assignment_id = user_role.id

        create_audit_log(
            request=request,
            action="role.remove",
            target_type="UserRole",
            target_id=assignment_id,
            metadata={
                "user_id": str(user.id),
                "user_email": user.email,
                "role_id": str(role.id),
                "role_name": role.name,
            },
        )

        user_role.delete()

        return Response(
            {
                "message": "Role removed successfully.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                },
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# PERMISSION LIST
# GET /api/auth/permissions/
# ============================================================

class PermissionListView(APIView):

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "permissions.view"

    def get(self, request):
        permissions = Permission.objects.all().order_by("codename")
        serializer = PermissionSerializer(permissions, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# ROLE PERMISSIONS
# GET    /api/auth/roles/<uuid:role_id>/permissions/
# POST   /api/auth/roles/<uuid:role_id>/permissions/
# PUT    /api/auth/roles/<uuid:role_id>/permissions/
#
# GET requires roles.view.
# POST / PUT require roles.manage.
# ============================================================

class RolePermissionView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, role_id):
        if not has_permission(request, "roles.view"):
            return Response(
                {
                    "detail": (
                        "You do not have permission to view role permissions."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            role = Role.objects.get(id=role_id)
        except (Role.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role_permissions = (
            RolePermission.objects
            .filter(role=role)
            .select_related("permission")
            .order_by("permission__codename")
        )

        data = [
            {
                "id": str(item.id),
                "permission": str(item.permission.id),
                "permission_name": item.permission.codename,
                "permission_description": item.permission.description,
            }
            for item in role_permissions
        ]

        return Response(
            {
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                },
                "permissions": data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, role_id):
        if not has_permission(request, "roles.manage"):
            return Response(
                {
                    "detail": (
                        "You do not have permission to manage role permissions."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            role = Role.objects.get(id=role_id)
        except (Role.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        permission_identifier = request.data.get("permission_id")

        if not permission_identifier:
            return Response(
                {"detail": "permission_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        permission = get_permission_by_identifier(
            permission_identifier
        )

        if permission is None:
            return Response(
                {"detail": "Permission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if RolePermission.objects.filter(
            role=role,
            permission=permission,
        ).exists():
            return Response(
                {
                    "detail": (
                        "Permission is already assigned to this role."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        role_permission = RolePermission.objects.create(
            role=role,
            permission=permission,
        )

        create_audit_log(
            request=request,
            action="permission.assign",
            target_type="RolePermission",
            target_id=role_permission.id,
            metadata={
                "role_id": str(role.id),
                "role_name": role.name,
                "permission_id": str(permission.id),
                "permission_name": permission.codename,
            },
        )

        return Response(
            {
                "message": "Permission assigned successfully.",
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },
                "permission": {
                    "id": str(permission.id),
                    "codename": permission.codename,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    def put(self, request, role_id):
        if not has_permission(request, "roles.manage"):
            return Response(
                {
                    "detail": (
                        "You do not have permission to manage role permissions."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            role = Role.objects.get(id=role_id)
        except (Role.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        permission_ids = request.data.get("permission_ids")

        if permission_ids is None:
            return Response(
                {"detail": "permission_ids is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(permission_ids, list):
            return Response(
                {"detail": "permission_ids must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolved_permissions = []
        invalid_identifiers = []
        seen_permission_ids = set()

        for identifier in permission_ids:
            permission = get_permission_by_identifier(identifier)

            if permission is None:
                invalid_identifiers.append(str(identifier))
                continue

            permission_id = str(permission.id)

            if permission_id not in seen_permission_ids:
                seen_permission_ids.add(permission_id)
                resolved_permissions.append(permission)

        if invalid_identifiers:
            return Response(
                {
                    "detail": "One or more permissions were not found.",
                    "invalid_permission_ids": invalid_identifiers,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_permissions = list(
            RolePermission.objects
            .filter(role=role)
            .select_related("permission")
            .order_by("permission__codename")
        )

        old_permissions = [
            {
                "id": str(item.permission.id),
                "codename": item.permission.codename,
            }
            for item in current_permissions
        ]

        new_permissions_data = [
            {
                "id": str(permission.id),
                "codename": permission.codename,
            }
            for permission in resolved_permissions
        ]

        with transaction.atomic():
            RolePermission.objects.filter(role=role).delete()

            RolePermission.objects.bulk_create([
                RolePermission(
                    role=role,
                    permission=permission,
                )
                for permission in resolved_permissions
            ])

            create_audit_log(
                request=request,
                action="role.permissions.update",
                target_type="Role",
                target_id=role.id,
                metadata={
                    "role_id": str(role.id),
                    "role_name": role.name,
                    "before": old_permissions,
                    "after": new_permissions_data,
                },
            )

        return Response(
            {
                "message": "Role permissions updated successfully.",
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },
                "permissions": new_permissions_data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# REMOVE PERMISSION FROM ROLE
# DELETE /api/auth/roles/<uuid:role_id>/permissions/<uuid:permission_id>/
# Requires roles.manage.
# ============================================================

class RolePermissionDetailView(APIView):

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "roles.manage"

    def delete(self, request, role_id, permission_id):
        try:
            role = Role.objects.get(id=role_id)
        except (Role.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            permission = Permission.objects.get(id=permission_id)
        except (Permission.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Permission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            role_permission = RolePermission.objects.get(
                role=role,
                permission=permission,
            )
        except RolePermission.DoesNotExist:
            return Response(
                {"detail": "Permission is not assigned to this role."},
                status=status.HTTP_404_NOT_FOUND,
            )

        assignment_id = role_permission.id

        create_audit_log(
            request=request,
            action="permission.remove",
            target_type="RolePermission",
            target_id=assignment_id,
            metadata={
                "role_id": str(role.id),
                "role_name": role.name,
                "permission_id": str(permission.id),
                "permission_name": permission.codename,
            },
        )

        role_permission.delete()

        return Response(
            {
                "message": "Permission removed successfully.",
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },
                "permission": {
                    "id": str(permission.id),
                    "codename": permission.codename,
                },
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# AUDIT LOGS
# GET /api/auth/audit-logs/
# ============================================================

class AuditLogListView(APIView):

    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "audit.view"

    def get(self, request):
        logs = (
            AuditLog.objects
            .select_related("actor")
            .all()
            .order_by("-created_at")
        )

        serializer = AuditLogSerializer(logs, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
