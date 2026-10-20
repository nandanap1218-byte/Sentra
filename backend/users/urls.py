from django.urls import path

from users.views import (
    RegisterView,
    LoginView,
    LogoutView,
    RefreshView,
    MeView,

    UserListView,
    UserDetailView,

    RoleListView,
    RoleDetailView,

    UserRoleView,
    UserRoleDetailView,

    PermissionListView,

    RolePermissionView,
    RolePermissionDetailView,

    AuditLogListView,
)


urlpatterns = [

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "login/",
        LoginView.as_view(),
        name="login"
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="logout"
    ),

    path(
        "refresh/",
        RefreshView.as_view(),
        name="token_refresh"
    ),

    path(
        "me/",
        MeView.as_view(),
        name="me"
    ),


    # ========================================================
    # USERS
    # ========================================================

    path(
        "users/",
        UserListView.as_view(),
        name="user-list"
    ),

    path(
        "users/<uuid:user_id>/",
        UserDetailView.as_view(),
        name="user-detail"
    ),


    # ========================================================
    # ROLES
    # ========================================================

    path(
        "roles/",
        RoleListView.as_view(),
        name="role-list"
    ),

    path(
        "roles/<uuid:role_id>/",
        RoleDetailView.as_view(),
        name="role-detail"
    ),


    # ========================================================
    # USER ROLE ASSIGNMENT
    # ========================================================

    path(
        "users/<uuid:user_id>/roles/",
        UserRoleView.as_view(),
        name="user-roles"
    ),

    path(
        "users/<uuid:user_id>/roles/<uuid:role_id>/",
        UserRoleDetailView.as_view(),
        name="user-role-detail"
    ),


    # ========================================================
    # PERMISSIONS
    # ========================================================

    path(
        "permissions/",
        PermissionListView.as_view(),
        name="permission-list"
    ),


    # ========================================================
    # ROLE PERMISSION MANAGEMENT
    # ========================================================

    path(
        "roles/<uuid:role_id>/permissions/",
        RolePermissionView.as_view(),
        name="role-permissions"
    ),

    path(
        "roles/<uuid:role_id>/permissions/<uuid:permission_id>/",
        RolePermissionDetailView.as_view(),
        name="role-permission-detail"
    ),


    # ========================================================
    # AUDIT LOGS
    # ========================================================

    path(
        "audit-logs/",
        AuditLogListView.as_view(),
        name="audit-logs"
    ),
]