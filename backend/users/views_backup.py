from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

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
# AUDIT LOG HELPER
# ============================================================

def create_audit_log(
    request,
    action,
    target_type,
    target_id=None,
    metadata=None
):
    """
    Automatically creates an audit log entry.
    """

    actor = (
        request.user
        if request.user and request.user.is_authenticated
        else None
    )

    ip_address = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if ip_address:
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.META.get(
            "REMOTE_ADDR"
        )

    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        ip_address=ip_address,
        metadata=metadata or {},
    )


# ============================================================
# REGISTER
# POST /api/auth/register/
# ============================================================

class RegisterView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()

            create_audit_log(
                request=request,
                action="user.register",
                target_type="User",
                target_id=user.id,
                metadata={
                    "email": user.email,
                    "full_name": user.full_name,
                }
            )

            return Response(
                {
                    "message": "User registered successfully.",

                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "full_name": user.full_name,
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
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
                {
                    "detail":
                    "Email and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Invalid email or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):

            return Response(
                {
                    "detail":
                    "Invalid email or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:

            return Response(
                {
                    "detail":
                    "User account is inactive."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        # Automatic audit log
        create_audit_log(
            request=request,
            action="user.login",
            target_type="User",
            target_id=user.id,
            metadata={
                "email": user.email,
            }
        )

        return Response(
            {
                "message": "Login successful.",

                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },

                "access": str(
                    refresh.access_token
                ),

                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

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
# AUDIT LOG HELPER
# ============================================================

def create_audit_log(
    request,
    action,
    target_type,
    target_id=None,
    metadata=None
):
    """
    Automatically creates an audit log entry.
    """

    actor = (
        request.user
        if request.user and request.user.is_authenticated
        else None
    )

    ip_address = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if ip_address:
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.META.get(
            "REMOTE_ADDR"
        )

    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        ip_address=ip_address,
        metadata=metadata or {},
    )


# ============================================================
# REGISTER
# POST /api/auth/register/
# ============================================================

class RegisterView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()

            create_audit_log(
                request=request,
                action="user.register",
                target_type="User",
                target_id=user.id,
                metadata={
                    "email": user.email,
                    "full_name": user.full_name,
                }
            )

            return Response(
                {
                    "message": "User registered successfully.",

                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "full_name": user.full_name,
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
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
                {
                    "detail":
                    "Email and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Invalid email or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):

            return Response(
                {
                    "detail":
                    "Invalid email or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:

            return Response(
                {
                    "detail":
                    "User account is inactive."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        # Automatic audit log
        create_audit_log(
            request=request,
            action="user.login",
            target_type="User",
            target_id=user.id,
            metadata={
                "email": user.email,
            }
        )

        return Response(
            {
                "message": "Login successful.",

                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },

                "access": str(
                    refresh.access_token
                ),

                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )

# ============================================================
# LOGOUT
# POST /api/auth/logout/
# ============================================================

class LogoutView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:

            return Response(
                {
                    "detail":
                    "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            token = RefreshToken(refresh_token)

            token.blacklist()

            create_audit_log(
                request=request,
                action="user.logout",
                target_type="User",
                target_id=request.user.id,
                metadata={
                    "email": request.user.email,
                }
            )

            return Response(
                {
                    "message":
                    "Logout successful."
                },
                status=status.HTTP_200_OK
            )

        except Exception:

            return Response(
                {
                    "detail":
                    "Invalid or already blacklisted refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
# ============================================================
# CURRENT USER
# GET /api/auth/me/
# ============================================================

class MeView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        user = request.user

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# USER LIST / CREATE
# ============================================================

class UserListView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    # --------------------------------------------------------
    # GET USERS
    # --------------------------------------------------------

    def get(self, request):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewUsersView",
                (),
                {
                    "required_permission":
                    "users.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        users = User.objects.all().order_by(
            "-created_at"
        )

        data = [
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at,
            }
            for user in users
        ]

        return Response(
            data,
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    def post(self, request):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "CreateUserView",
                (),
                {
                    "required_permission":
                    "users.create"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to create users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserCreateSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()

            create_audit_log(
                request=request,
                action="user.create",
                target_type="User",
                target_id=user.id,
                metadata={
                    "email": user.email,
                    "full_name": user.full_name,
                }
            )

            return Response(
                {
                    "message":
                    "User created successfully.",

                    "user":
                    UserDetailSerializer(user).data,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# USER DETAIL
# ============================================================

class UserDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get_user(self, user_id):

        try:

            return User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return None

    # --------------------------------------------------------
    # GET USER
    # --------------------------------------------------------

    def get(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewUserView",
                (),
                {
                    "required_permission":
                    "users.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_user(user_id)

        if user is None:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserDetailSerializer(user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # PATCH USER
    # --------------------------------------------------------

    def patch(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "EditUserView",
                (),
                {
                    "required_permission":
                    "users.edit"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to edit users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_user(user_id)

        if user is None:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        old_data = {
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
        }

        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

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
                    }
                }
            )

            return Response(
                {
                    "message":
                    "User updated successfully.",

                    "user":
                    UserDetailSerializer(user).data,
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # DELETE USER
    # --------------------------------------------------------

    def delete(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "DeleteUserView",
                (),
                {
                    "required_permission":
                    "users.delete"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to delete users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_user(user_id)

        if user is None:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        email = user.email

        user.delete()

        create_audit_log(
            request=request,
            action="user.delete",
            target_type="User",
            target_id=user_id,
            metadata={
                "email": email,
            }
        )

        return Response(
            {
                "message":
                "User deleted successfully."
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# ROLE LIST / CREATE
#
# GET  /api/auth/roles/
# POST /api/auth/roles/
# ============================================================

class RoleListView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    # --------------------------------------------------------
    # GET - List all roles
    # --------------------------------------------------------

    def get(self, request):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewRolesView",
                (),
                {
                    "required_permission": "roles.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view roles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        roles = Role.objects.all().order_by(
            "name"
        )

        data = []

        for role in roles:

            role_permissions = (
                RolePermission.objects
                .filter(role=role)
                .select_related("permission")
            )

            permissions = [
                item.permission.codename
                for item in role_permissions
            ]

            data.append(
                {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                    "is_system": role.is_system,
                    "permissions": permissions,
                }
            )

        return Response(
            data,
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # POST - Create a new role
    # --------------------------------------------------------

    def post(self, request):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "CreateRoleView",
                (),
                {
                    "required_permission":
                    "roles.manage"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to create roles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RoleSerializer(
            data=request.data
        )

        if serializer.is_valid():

            role = serializer.save()

            create_audit_log(
                request=request,
                action="role.create",
                target_type="Role",
                target_id=role.id,
                metadata={
                    "name": role.name,
                    "description": role.description,
                }
            )

            return Response(
                {
                    "message":
                    "Role created successfully.",

                    "role":
                    RoleSerializer(role).data,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class RoleDetailView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get_role(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return None

    def get(self, request, role_id):
        permission = HasPermission()
        if not permission.has_permission(
            request,
            type("View", (), {"required_permission": "roles.view"})()
        ):
            return Response(
                {"detail": "You do not have permission to view roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if not role:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RoleSerializer(role)
        return Response(serializer.data)

    def patch(self, request, role_id):
        permission = HasPermission()
        if not permission.has_permission(
            request,
            type("View", (), {"required_permission": "roles.manage"})()
        ):
            return Response(
                {"detail": "You do not have permission to manage roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if not role:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if role.is_system:
            return Response(
                {"detail": "System roles cannot be modified."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RoleSerializer(
            role,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            updated_role = serializer.save()

            create_audit_log(
                actor=request.user,
                action="role.update",
                target_type="role",
                target_id=str(updated_role.id),
                request=request,
                metadata={
                    "after": RoleSerializer(updated_role).data,
                },
            )

            return Response(
                RoleSerializer(updated_role).data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, role_id):
        permission = HasPermission()
        if not permission.has_permission(
            request,
            type("View", (), {"required_permission": "roles.manage"})()
        ):
            return Response(
                {"detail": "You do not have permission to manage roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if not role:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if role.is_system:
            return Response(
                {"detail": "System roles cannot be modified."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role_id_str = str(role.id)
        role_name = role.name

        role.delete()

        create_audit_log(
            actor=request.user,
            action="role.delete",
            target_type="role",
            target_id=role_id_str,
            request=request,
            metadata={
                "name": role_name,
            },
        )

        return Response(
            {"detail": "Role deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
# ============================================================
# USER ROLE ASSIGNMENT
# ============================================================

class UserRoleView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    # --------------------------------------------------------
    # GET USER ROLES
    # Requires: roles.view
    # --------------------------------------------------------

    def get(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewUserRolesView",
                (),
                {
                    "required_permission": "roles.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view user roles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        user_roles = (
            UserRole.objects
            .filter(user=user)
            .select_related("role")
        )

        serializer = UserRoleDetailSerializer(
            user_roles,
            many=True
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
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # POST ASSIGN ROLE
    # Requires: roles.manage
    # --------------------------------------------------------

    def post(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "AssignUserRoleView",
                (),
                {
                    "required_permission": "roles.manage"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to assign roles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        role_id = request.data.get(
            "role_id"
        )

        if not role_id:

            return Response(
                {
                    "detail":
                    "role_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        existing_assignment = (
            UserRole.objects.filter(
                user=user,
                role=role
            ).exists()
        )

        if existing_assignment:

            return Response(
                {
                    "detail":
                    "Role is already assigned "
                    "to this user."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user_role = UserRole.objects.create(
            user=user,
            role=role
        )

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
            }
        )

        return Response(
            {
                "message":
                "Role assigned successfully.",

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
                    "assigned_at":
                    user_role.assigned_at,
                },
            },
            status=status.HTTP_201_CREATED
        )

# ============================================================
# USER ROLE DETAIL
# DELETE
# ============================================================

class UserRoleDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        HasPermission,
    ]

    required_permission = "roles.manage"

    def delete(
        self,
        request,
        user_id,
        role_id
    ):

        try:

            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            user_role = UserRole.objects.get(
                user=user,
                role=role
            )

        except UserRole.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Role is not assigned "
                    "to this user."
                },
                status=status.HTTP_404_NOT_FOUND
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
            }
        )

        user_role.delete()

        return Response(
            {
                "message":
                "Role removed successfully.",

                "user": {
                    "id": str(user.id),
                    "email": user.email,
                },

                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# PERMISSION LIST
# GET /api/auth/permissions/
# ============================================================

class PermissionListView(APIView):

    permission_classes = [
        IsAuthenticated,
        HasPermission,
    ]

    required_permission = "permissions.view"

    def get(self, request):

        permissions = Permission.objects.all().order_by(
            "codename"
        )

        serializer = PermissionSerializer(
            permissions,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class RolePermissionView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    # --------------------------------------------------------
    # GET ROLE PERMISSIONS
    # Requires: roles.view
    # --------------------------------------------------------

    def get(self, request, role_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewRolePermissionsView",
                (),
                {
                    "required_permission": "roles.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view role permissions."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        role_permissions = (
            RolePermission.objects
            .filter(role=role)
            .select_related("permission")
            .order_by("permission__codename")
        )

        data = []

        for item in role_permissions:

            data.append(
                {
                    "id": str(item.id),

                    "permission": str(
                        item.permission.id
                    ),

                    "permission_name":
                    item.permission.codename,

                    "permission_description":
                    item.permission.description,
                }
            )

        return Response(
            {
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                },

                "permissions": data,
            },
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # ASSIGN PERMISSION
    # Requires: roles.manage
    # --------------------------------------------------------

    def post(self, request, role_id):

        permission_checker = HasPermission()

        allowed = permission_checker.has_permission(
            request,
            type(
                "AssignRolePermissionView",
                (),
                {
                    "required_permission": "roles.manage"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to manage role permissions."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if role.is_system:

            return Response(
                {
                    "detail":
                    "System roles cannot be modified."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        permission_id = request.data.get(
            "permission_id"
        )

        if not permission_id:

            return Response(
                {
                    "detail":
                    "permission_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            permission = Permission.objects.get(
                id=permission_id
            )

        except Permission.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Permission not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        existing = RolePermission.objects.filter(
            role=role,
            permission=permission
        ).exists()

        if existing:

            return Response(
                {
                    "detail":
                    "Permission is already assigned "
                    "to this role."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        role_permission = RolePermission.objects.create(
            role=role,
            permission=permission
        )

        create_audit_log(
            request=request,
            action="permission.assign",
            target_type="RolePermission",
            target_id=role_permission.id,
            metadata={
                "role_id": str(role.id),
                "role_name": role.name,
                "permission_id":
                    str(permission.id),
                "permission_name":
                    permission.codename,
            }
        )

        return Response(
            {
                "message":
                "Permission assigned successfully.",

                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },

                "permission": {
                    "id": str(permission.id),
                    "codename":
                        permission.codename,
                },
            },
            status=status.HTTP_201_CREATED
        )
# ============================================================
# REMOVE PERMISSION FROM ROLE
# ============================================================

class RolePermissionDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        HasPermission,
    ]

    required_permission = "roles.manage"

    def delete(
        self,
        request,
        role_id,
        permission_id
    ):

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if role.is_system:

            return Response(
                {
                    "detail":
                    "System roles cannot be modified."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            permission = Permission.objects.get(
                id=permission_id
            )

        except Permission.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Permission not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            role_permission = (
                RolePermission.objects.get(
                    role=role,
                    permission=permission
                )
            )

        except RolePermission.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Permission is not assigned "
                    "to this role."
                },
                status=status.HTTP_404_NOT_FOUND
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
                "permission_id":
                    str(permission.id),
                "permission_name":
                    permission.codename,
            }
        )

        role_permission.delete()

        return Response(
            {
                "message":
                "Permission removed successfully.",

                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },

                "permission": {
                    "id": str(permission.id),
                    "codename":
                    permission.codename,
                },
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# AUDIT LOGS
# GET /api/auth/audit-logs/
# ============================================================

class AuditLogListView(APIView):

    permission_classes = [
        IsAuthenticated,
        HasPermission,
    ]

    required_permission = "audit.view"

    def get(self, request):

        logs = (
            AuditLog.objects
            .select_related("actor")
            .all()
            .order_by("-created_at")
        )

        serializer = AuditLogSerializer(
            logs,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
# ============================================================
# CURRENT USER
# GET /api/auth/me/
# ============================================================

class MeView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        user = request.user

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# USER LIST / CREATE
# ============================================================

class UserListView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    # --------------------------------------------------------
    # GET USERS
    # --------------------------------------------------------

    def get(self, request):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewUsersView",
                (),
                {
                    "required_permission":
                    "users.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        users = User.objects.all().order_by(
            "-created_at"
        )

        data = [
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at,
            }
            for user in users
        ]

        return Response(
            data,
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    def post(self, request):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "CreateUserView",
                (),
                {
                    "required_permission":
                    "users.create"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to create users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserCreateSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()

            create_audit_log(
                request=request,
                action="user.create",
                target_type="User",
                target_id=user.id,
                metadata={
                    "email": user.email,
                    "full_name": user.full_name,
                }
            )

            return Response(
                {
                    "message":
                    "User created successfully.",

                    "user":
                    UserDetailSerializer(user).data,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# USER DETAIL
# ============================================================

class UserDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get_user(self, user_id):

        try:

            return User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return None

    # --------------------------------------------------------
    # GET USER
    # --------------------------------------------------------

    def get(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewUserView",
                (),
                {
                    "required_permission":
                    "users.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_user(user_id)

        if user is None:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserDetailSerializer(user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # PATCH USER
    # --------------------------------------------------------

    def patch(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "EditUserView",
                (),
                {
                    "required_permission":
                    "users.edit"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to edit users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_user(user_id)

        if user is None:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        old_data = {
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
        }

        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

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
                    }
                }
            )

            return Response(
                {
                    "message":
                    "User updated successfully.",

                    "user":
                    UserDetailSerializer(user).data,
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # DELETE USER
    # --------------------------------------------------------

    def delete(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "DeleteUserView",
                (),
                {
                    "required_permission":
                    "users.delete"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to delete users."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_user(user_id)

        if user is None:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        email = user.email

        user.delete()

        create_audit_log(
            request=request,
            action="user.delete",
            target_type="User",
            target_id=user_id,
            metadata={
                "email": email,
            }
        )

        return Response(
            {
                "message":
                "User deleted successfully."
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# ROLE LIST / CREATE
#
# GET  /api/auth/roles/
# POST /api/auth/roles/
# ============================================================

class RoleListView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    # --------------------------------------------------------
    # GET - List all roles
    # --------------------------------------------------------

    def get(self, request):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewRolesView",
                (),
                {
                    "required_permission": "roles.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view roles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        roles = Role.objects.all().order_by(
            "name"
        )

        data = []

        for role in roles:

            role_permissions = (
                RolePermission.objects
                .filter(role=role)
                .select_related("permission")
            )

            permissions = [
                item.permission.codename
                for item in role_permissions
            ]

            data.append(
                {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                    "is_system": role.is_system,
                    "permissions": permissions,
                }
            )

        return Response(
            data,
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # POST - Create a new role
    # --------------------------------------------------------

    def post(self, request):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "CreateRoleView",
                (),
                {
                    "required_permission":
                    "roles.manage"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to create roles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RoleSerializer(
            data=request.data
        )

        if serializer.is_valid():

            role = serializer.save()

            create_audit_log(
                request=request,
                action="role.create",
                target_type="Role",
                target_id=role.id,
                metadata={
                    "name": role.name,
                    "description": role.description,
                }
            )

            return Response(
                {
                    "message":
                    "Role created successfully.",

                    "role":
                    RoleSerializer(role).data,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class RoleDetailView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get_role(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return None

    def get(self, request, role_id):
        permission = HasPermission()
        if not permission.has_permission(
            request,
            type("View", (), {"required_permission": "roles.view"})()
        ):
            return Response(
                {"detail": "You do not have permission to view roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if not role:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RoleSerializer(role)
        return Response(serializer.data)

    def patch(self, request, role_id):
        permission = HasPermission()
        if not permission.has_permission(
            request,
            type("View", (), {"required_permission": "roles.manage"})()
        ):
            return Response(
                {"detail": "You do not have permission to manage roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if not role:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if role.is_system:
            return Response(
                {"detail": "System roles cannot be modified."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RoleSerializer(
            role,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            updated_role = serializer.save()

            create_audit_log(
                actor=request.user,
                action="role.update",
                target_type="role",
                target_id=str(updated_role.id),
                request=request,
                metadata={
                    "after": RoleSerializer(updated_role).data,
                },
            )

            return Response(
                RoleSerializer(updated_role).data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, role_id):
        permission = HasPermission()
        if not permission.has_permission(
            request,
            type("View", (), {"required_permission": "roles.manage"})()
        ):
            return Response(
                {"detail": "You do not have permission to manage roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_role(role_id)

        if not role:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if role.is_system:
            return Response(
                {"detail": "System roles cannot be modified."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role_id_str = str(role.id)
        role_name = role.name

        role.delete()

        create_audit_log(
            actor=request.user,
            action="role.delete",
            target_type="role",
            target_id=role_id_str,
            request=request,
            metadata={
                "name": role_name,
            },
        )

        return Response(
            {"detail": "Role deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
# ============================================================
# USER ROLE ASSIGNMENT
# ============================================================

class UserRoleView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    # --------------------------------------------------------
    # GET USER ROLES
    # Requires: roles.view
    # --------------------------------------------------------

    def get(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewUserRolesView",
                (),
                {
                    "required_permission": "roles.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view user roles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        user_roles = (
            UserRole.objects
            .filter(user=user)
            .select_related("role")
        )

        serializer = UserRoleDetailSerializer(
            user_roles,
            many=True
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
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # POST ASSIGN ROLE
    # Requires: roles.manage
    # --------------------------------------------------------

    def post(self, request, user_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "AssignUserRoleView",
                (),
                {
                    "required_permission": "roles.manage"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to assign roles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        role_id = request.data.get(
            "role_id"
        )

        if not role_id:

            return Response(
                {
                    "detail":
                    "role_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        existing_assignment = (
            UserRole.objects.filter(
                user=user,
                role=role
            ).exists()
        )

        if existing_assignment:

            return Response(
                {
                    "detail":
                    "Role is already assigned "
                    "to this user."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user_role = UserRole.objects.create(
            user=user,
            role=role
        )

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
            }
        )

        return Response(
            {
                "message":
                "Role assigned successfully.",

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
                    "assigned_at":
                    user_role.assigned_at,
                },
            },
            status=status.HTTP_201_CREATED
        )

# ============================================================
# USER ROLE DETAIL
# DELETE
# ============================================================

class UserRoleDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        HasPermission,
    ]

    required_permission = "roles.manage"

    def delete(
        self,
        request,
        user_id,
        role_id
    ):

        try:

            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            user_role = UserRole.objects.get(
                user=user,
                role=role
            )

        except UserRole.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Role is not assigned "
                    "to this user."
                },
                status=status.HTTP_404_NOT_FOUND
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
            }
        )

        user_role.delete()

        return Response(
            {
                "message":
                "Role removed successfully.",

                "user": {
                    "id": str(user.id),
                    "email": user.email,
                },

                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# PERMISSION LIST
# GET /api/auth/permissions/
# ============================================================

class PermissionListView(APIView):

    permission_classes = [
        IsAuthenticated,
        HasPermission,
    ]

    required_permission = "permissions.view"

    def get(self, request):

        permissions = Permission.objects.all().order_by(
            "codename"
        )

        serializer = PermissionSerializer(
            permissions,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class RolePermissionView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    # --------------------------------------------------------
    # GET ROLE PERMISSIONS
    # Requires: roles.view
    # --------------------------------------------------------

    def get(self, request, role_id):

        permission = HasPermission()

        allowed = permission.has_permission(
            request,
            type(
                "ViewRolePermissionsView",
                (),
                {
                    "required_permission": "roles.view"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to view role permissions."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        role_permissions = (
            RolePermission.objects
            .filter(role=role)
            .select_related("permission")
            .order_by("permission__codename")
        )

        data = []

        for item in role_permissions:

            data.append(
                {
                    "id": str(item.id),

                    "permission": str(
                        item.permission.id
                    ),

                    "permission_name":
                    item.permission.codename,

                    "permission_description":
                    item.permission.description,
                }
            )

        return Response(
            {
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                },

                "permissions": data,
            },
            status=status.HTTP_200_OK
        )

    # --------------------------------------------------------
    # ASSIGN PERMISSION
    # Requires: roles.manage
    # --------------------------------------------------------

    def post(self, request, role_id):

        permission_checker = HasPermission()

        allowed = permission_checker.has_permission(
            request,
            type(
                "AssignRolePermissionView",
                (),
                {
                    "required_permission": "roles.manage"
                }
            )
        )

        if not allowed:

            return Response(
                {
                    "detail":
                    "You do not have permission "
                    "to manage role permissions."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if role.is_system:

            return Response(
                {
                    "detail":
                    "System roles cannot be modified."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        permission_id = request.data.get(
            "permission_id"
        )

        if not permission_id:

            return Response(
                {
                    "detail":
                    "permission_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            permission = Permission.objects.get(
                id=permission_id
            )

        except Permission.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Permission not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        existing = RolePermission.objects.filter(
            role=role,
            permission=permission
        ).exists()

        if existing:

            return Response(
                {
                    "detail":
                    "Permission is already assigned "
                    "to this role."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        role_permission = RolePermission.objects.create(
            role=role,
            permission=permission
        )

        create_audit_log(
            request=request,
            action="permission.assign",
            target_type="RolePermission",
            target_id=role_permission.id,
            metadata={
                "role_id": str(role.id),
                "role_name": role.name,
                "permission_id":
                    str(permission.id),
                "permission_name":
                    permission.codename,
            }
        )

        return Response(
            {
                "message":
                "Permission assigned successfully.",

                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },

                "permission": {
                    "id": str(permission.id),
                    "codename":
                        permission.codename,
                },
            },
            status=status.HTTP_201_CREATED
        )
# ============================================================
# REMOVE PERMISSION FROM ROLE
# ============================================================

class RolePermissionDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
        HasPermission,
    ]

    required_permission = "roles.manage"

    def delete(
        self,
        request,
        role_id,
        permission_id
    ):

        try:

            role = Role.objects.get(
                id=role_id
            )

        except Role.DoesNotExist:

            return Response(
                {
                    "detail": "Role not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if role.is_system:

            return Response(
                {
                    "detail":
                    "System roles cannot be modified."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            permission = Permission.objects.get(
                id=permission_id
            )

        except Permission.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Permission not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            role_permission = (
                RolePermission.objects.get(
                    role=role,
                    permission=permission
                )
            )

        except RolePermission.DoesNotExist:

            return Response(
                {
                    "detail":
                    "Permission is not assigned "
                    "to this role."
                },
                status=status.HTTP_404_NOT_FOUND
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
                "permission_id":
                    str(permission.id),
                "permission_name":
                    permission.codename,
            }
        )

        role_permission.delete()

        return Response(
            {
                "message":
                "Permission removed successfully.",

                "role": {
                    "id": str(role.id),
                    "name": role.name,
                },

                "permission": {
                    "id": str(permission.id),
                    "codename":
                    permission.codename,
                },
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# AUDIT LOGS
# GET /api/auth/audit-logs/
# ============================================================

class AuditLogListView(APIView):

    permission_classes = [
        IsAuthenticated,
        HasPermission,
    ]

    required_permission = "audit.view"

    def get(self, request):

        logs = (
            AuditLog.objects
            .select_related("actor")
            .all()
            .order_by("-created_at")
        )

        serializer = AuditLogSerializer(
            logs,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )