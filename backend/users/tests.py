from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import (
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
)


# ============================================================
# MODEL TESTS
# ============================================================

class UserModelTests(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(
            email="modeluser@example.com",
            full_name="Model Test User",
            password="TestPassword@123",
        )

        self.assertEqual(user.email, "modeluser@example.com")
        self.assertEqual(user.full_name, "Model Test User")
        self.assertTrue(user.check_password("TestPassword@123"))


class RoleModelTests(TestCase):

    def test_create_role(self):
        role = Role.objects.create(
            name="Model Test Role",
            description="Model role testing",
            is_system=False,
        )

        self.assertEqual(role.name, "Model Test Role")
        self.assertFalse(role.is_system)


class PermissionModelTests(TestCase):

    def test_create_permission(self):
        permission = Permission.objects.create(
            codename="model.test",
            description="Model permission testing",
        )

        self.assertEqual(permission.codename, "model.test")


class UserRoleModelTests(TestCase):

    def test_create_user_role(self):
        user = User.objects.create_user(
            email="userrole@example.com",
            full_name="User Role Test",
            password="TestPassword@123",
        )

        role = Role.objects.create(
            name="User Role Test Role",
            description="Testing user role",
            is_system=False,
        )

        user_role = UserRole.objects.create(
            user=user,
            role=role,
        )

        self.assertEqual(user_role.user, user)
        self.assertEqual(user_role.role, role)


class RolePermissionModelTests(TestCase):

    def test_create_role_permission(self):
        role = Role.objects.create(
            name="Role Permission Test Role",
            description="Testing role permission",
            is_system=False,
        )

        permission = Permission.objects.create(
            codename="role.permission.test",
            description="Testing role permission",
        )

        role_permission = RolePermission.objects.create(
            role=role,
            permission=permission,
        )

        self.assertEqual(role_permission.role, role)
        self.assertEqual(role_permission.permission, permission)


# ============================================================
# REGISTRATION API TESTS
# ============================================================

class RegistrationAPITests(APITestCase):

    def test_user_registration(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "newuser@example.com",
                "full_name": "New Test User",
                "password": "TestPassword@123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["user"]["email"],
            "newuser@example.com",
        )

        self.assertEqual(
            response.data["user"]["full_name"],
            "New Test User",
        )

        self.assertTrue(
            User.objects.filter(
                email="newuser@example.com"
            ).exists()
        )

    def test_duplicate_email_registration(self):
        User.objects.create_user(
            email="existing@example.com",
            full_name="Existing User",
            password="TestPassword@123",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "existing@example.com",
                "full_name": "Another User",
                "password": "TestPassword@123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


# ============================================================
# LOGIN API TESTS
# ============================================================

class LoginAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="loginuser@example.com",
            full_name="Login Test User",
            password="TestPassword@123",
        )

    def test_successful_login(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "loginuser@example.com",
                "password": "TestPassword@123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_invalid_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "loginuser@example.com",
                "password": "WrongPassword@123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


# ============================================================
# CURRENT USER / ME API TESTS
# ============================================================

class MeAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="meuser@example.com",
            full_name="Me Test User",
            password="TestPassword@123",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_get_current_user(self):
        response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            "meuser@example.com",
        )

        self.assertEqual(
            response.data["full_name"],
            "Me Test User",
        )

    def test_get_current_user_without_authentication(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


# ============================================================
# USERS LIST API TESTS
# ============================================================

class UsersListAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="listuser@example.com",
            full_name="List Test User",
            password="TestPassword@123",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_users_list_without_permission(self):
        response = self.client.get(
            "/api/auth/users/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class UsersListPermissionAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="viewerlist@example.com",
            full_name="Viewer List User",
            password="TestPassword@123",
        )

        self.role = Role.objects.create(
            name="List Viewer Role",
            description="Role for users list testing",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="users.view",
            description="View users",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_users_list_with_permission(self):
        User.objects.create_user(
            email="anotheruser@example.com",
            full_name="Another Test User",
            password="TestPassword@123",
        )

        response = self.client.get(
            "/api/auth/users/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertGreaterEqual(
            len(response.data),
            2,
        )


# ============================================================
# USER CREATION API TESTS
# ============================================================

class UserCreationAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="createuser@example.com",
            full_name="Create Test User",
            password="TestPassword@123",
        )

        self.role = Role.objects.create(
            name="Create User Role",
            description="Role for user creation testing",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="users.create",
            description="Create users",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_create_user_with_permission(self):
        response = self.client.post(
            "/api/auth/users/",
            {
                "email": "createduser@example.com",
                "full_name": "Created Test User",
                "password": "TestPassword@123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            User.objects.filter(
                email="createduser@example.com"
            ).exists()
        )


# ============================================================
# USER UPDATE API TESTS
# ============================================================

class UserUpdateAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="edituser@example.com",
            full_name="Edit Test User",
            password="TestPassword@123",
        )

        self.target_user = User.objects.create_user(
            email="targetuser@example.com",
            full_name="Original Name",
            password="TestPassword@123",
        )

        self.role = Role.objects.create(
            name="Edit User Role",
            description="Role for user update testing",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="users.edit",
            description="Edit users",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_update_user_with_permission(self):
        response = self.client.patch(
            f"/api/auth/users/{self.target_user.id}/",
            {
                "full_name": "Updated Test User"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.target_user.refresh_from_db()

        self.assertEqual(
            self.target_user.full_name,
            "Updated Test User",
        )


# ============================================================
# USER DELETE API TESTS
# ============================================================

class UserDeleteAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="deleteuser@example.com",
            full_name="Delete Test User",
            password="TestPassword@123",
        )

        self.target_user = User.objects.create_user(
            email="targetdelete@example.com",
            full_name="Target Delete User",
            password="TestPassword@123",
        )

        self.role = Role.objects.create(
            name="Delete User Role",
            description="Role for user deletion testing",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="users.delete",
            description="Delete users",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_delete_user_with_permission(self):
        user_id = self.target_user.id

        response = self.client.delete(
            f"/api/auth/users/{user_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            User.objects.filter(
                id=user_id
            ).exists()
        )


class UserDeletePermissionAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="nodeleteuser@example.com",
            full_name="No Delete User",
            password="TestPassword@123",
        )

        self.target_user = User.objects.create_user(
            email="protecteduser@example.com",
            full_name="Protected User",
            password="TestPassword@123",
        )

        self.role = Role.objects.create(
            name="View Only Delete Test Role",
            description="Role without delete permission",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="users.view",
            description="View users",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_delete_user_without_permission(self):
        user_id = self.target_user.id

        response = self.client.delete(
            f"/api/auth/users/{user_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            User.objects.filter(
                id=user_id
            ).exists()
        )


# ============================================================
# ROLES LIST API TESTS
# ============================================================

class RolesListAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="roleview@example.com",
            full_name="Role View User",
            password="TestPassword@123",
        )

        self.role = Role.objects.create(
            name="Role View Test Role",
            description="Role for roles list testing",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.view",
            description="View roles",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_roles_list_with_permission(self):
        response = self.client.get(
            "/api/auth/roles/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertGreaterEqual(
            len(response.data),
            1,
        )


# ============================================================
# ROLE CREATION API TESTS
# ============================================================

class RoleCreationAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="rolecreate@example.com",
            full_name="Role Create User",
            password="TestPassword@123",
        )

        self.role = Role.objects.create(
            name="Role Manager Test Role",
            description="Role for role creation testing",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_create_role_with_permission(self):
        response = self.client.post(
            "/api/auth/roles/",
            {
                "name": "New Test Role",
                "description": "Created during automated testing",
                "is_system": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Role.objects.filter(
                name="New Test Role"
            ).exists()
        )
# ============================================================
# ROLE CREATION PERMISSION DENIAL TESTS
# ============================================================

class RoleCreationPermissionAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="norolecreate@example.com",
            full_name="No Role Create User",
            password="TestPassword@123",
        )

        self.role = Role.objects.create(
            name="Role View Only Test Role",
            description="Role without manage permission",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.view",
            description="View roles",
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_create_role_without_permission(self):
        response = self.client.post(
            "/api/auth/roles/",
            {
                "name": "Unauthorized Test Role",
                "description": "This role should not be created",
                "is_system": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            Role.objects.filter(
                name="Unauthorized Test Role"
            ).exists()
        )
# ============================================================
# SYSTEM ROLE PROTECTION TESTS
# ============================================================

class SystemRoleUpdateAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="systemroleupdate@example.com",
            full_name="System Role Update User",
            password="TestPassword@123",
        )

        self.manage_role = Role.objects.create(
            name="System Role Manager",
            description="Role with role management permission",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manage_role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.manage_role,
        )

        self.system_role = Role.objects.create(
            name="System Protected Role",
            description="Protected system role",
            is_system=True,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_update_system_role(self):
        response = self.client.patch(
            f"/api/auth/roles/{self.system_role.id}/",
            {
                "description": "This should not be allowed"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.system_role.refresh_from_db()

        self.assertEqual(
            self.system_role.description,
            "Protected system role",
        )
# ============================================================
# SYSTEM ROLE DELETE PROTECTION TESTS
# ============================================================

class SystemRoleDeleteAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="systemroledelete@example.com",
            full_name="System Role Delete User",
            password="TestPassword@123",
        )

        self.manage_role = Role.objects.create(
            name="System Role Delete Manager",
            description="Role with role management permission",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manage_role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.manage_role,
        )

        self.system_role = Role.objects.create(
            name="System Protected Delete Role",
            description="Protected system role",
            is_system=True,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_delete_system_role(self):

        response = self.client.delete(
            f"/api/auth/roles/{self.system_role.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Role.objects.filter(
                id=self.system_role.id
            ).exists()
        )
# ============================================================
# USER ROLE ASSIGNMENT TESTS
# ============================================================

class UserRoleAssignmentAPITests(APITestCase):

    def setUp(self):
        self.manager = User.objects.create_user(
            email="roleassignmanager@example.com",
            full_name="Role Assign Manager",
            password="TestPassword@123",
        )

        self.target_user = User.objects.create_user(
            email="roleassigntarget@example.com",
            full_name="Role Assign Target",
            password="TestPassword@123",
        )

        self.manager_role = Role.objects.create(
            name="Role Assignment Manager",
            description="Role with role management permission",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manager_role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.manager,
            role=self.manager_role,
        )

        self.target_role = Role.objects.create(
            name="Assigned Test Role",
            description="Role to be assigned",
            is_system=False,
        )

        self.client.force_authenticate(
            user=self.manager
        )

    def test_assign_role_to_user(self):

        response = self.client.post(
            f"/api/auth/users/{self.target_user.id}/roles/",
            {
                "role_id": str(self.target_role.id)
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            UserRole.objects.filter(
                user=self.target_user,
                role=self.target_role,
            ).exists()
        )
# ============================================================
# DUPLICATE USER ROLE ASSIGNMENT TESTS
# ============================================================

class DuplicateUserRoleAssignmentAPITests(APITestCase):

    def setUp(self):
        self.manager = User.objects.create_user(
            email="duplicateassignmanager@example.com",
            full_name="Duplicate Assign Manager",
            password="TestPassword@123",
        )

        self.target_user = User.objects.create_user(
            email="duplicateassigntarget@example.com",
            full_name="Duplicate Assign Target",
            password="TestPassword@123",
        )

        self.manager_role = Role.objects.create(
            name="Duplicate Assignment Manager",
            description="Role with role management permission",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manager_role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.manager,
            role=self.manager_role,
        )

        self.target_role = Role.objects.create(
            name="Duplicate Assigned Role",
            description="Role for duplicate assignment testing",
            is_system=False,
        )

        # First assignment
        UserRole.objects.create(
            user=self.target_user,
            role=self.target_role,
        )

        self.client.force_authenticate(
            user=self.manager
        )

    def test_duplicate_role_assignment(self):

        response = self.client.post(
            f"/api/auth/users/{self.target_user.id}/roles/",
            {
                "role_id": str(self.target_role.id)
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            UserRole.objects.filter(
                user=self.target_user,
                role=self.target_role,
            ).count(),
            1,
        )
# ============================================================
# USER ROLE REMOVAL TESTS
# ============================================================

class UserRoleRemovalAPITests(APITestCase):

    def setUp(self):
        self.manager = User.objects.create_user(
            email="roleremovemanager@example.com",
            full_name="Role Remove Manager",
            password="TestPassword@123",
        )

        self.target_user = User.objects.create_user(
            email="roleremovetarget@example.com",
            full_name="Role Remove Target",
            password="TestPassword@123",
        )

        self.manager_role = Role.objects.create(
            name="Role Removal Manager",
            description="Role with role management permission",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manager_role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.manager,
            role=self.manager_role,
        )

        self.target_role = Role.objects.create(
            name="Role To Remove",
            description="Role for removal testing",
            is_system=False,
        )

        self.user_role = UserRole.objects.create(
            user=self.target_user,
            role=self.target_role,
        )

        self.client.force_authenticate(
            user=self.manager
        )

    def test_remove_role_from_user(self):

        response = self.client.delete(
            f"/api/auth/users/{self.target_user.id}/roles/"
            f"{self.target_role.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            UserRole.objects.filter(
                user=self.target_user,
                role=self.target_role,
            ).exists()
        )
# ============================================================
# USER ROLE REMOVAL PERMISSION DENIAL TESTS
# ============================================================

class UserRoleRemovalPermissionAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="noroleremove@example.com",
            full_name="No Role Remove User",
            password="TestPassword@123",
        )

        self.target_user = User.objects.create_user(
            email="protectedroleremove@example.com",
            full_name="Protected Role User",
            password="TestPassword@123",
        )

        self.view_role = Role.objects.create(
            name="Role View Only Removal",
            description="Role without manage permission",
            is_system=False,
        )

        self.permission = Permission.objects.create(
            codename="roles.view",
            description="View roles",
        )

        RolePermission.objects.create(
            role=self.view_role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.view_role,
        )

        self.target_role = Role.objects.create(
            name="Protected Assigned Role",
            description="Role that should not be removed",
            is_system=False,
        )

        UserRole.objects.create(
            user=self.target_user,
            role=self.target_role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_remove_role_without_permission(self):

        response = self.client.delete(
            f"/api/auth/users/{self.target_user.id}/roles/"
            f"{self.target_role.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            UserRole.objects.filter(
                user=self.target_user,
                role=self.target_role,
            ).exists()
        )
# ============================================================
# PERMISSION LIST API TESTS
# ============================================================

class PermissionListAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="permissionview@example.com",
            full_name="Permission View User",
            password="TestPassword@123",
        )

        self.permission = Permission.objects.create(
            codename="permissions.view",
            description="View permissions",
        )

        self.role = Role.objects.create(
            name="Permission Viewer",
            description="Can view permissions",
            is_system=False,
        )

        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.role,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_permission_list_with_permission(self):

        response = self.client.get(
            "/api/auth/permissions/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            any(
                item["codename"] == "permissions.view"
                for item in response.data
            )
        )

    def test_permission_list_without_permission(self):

        user_without_permission = User.objects.create_user(
            email="nopermissionview@example.com",
            full_name="No Permission View User",
            password="TestPassword@123",
        )

        self.client.force_authenticate(
            user=user_without_permission
        )

        response = self.client.get(
            "/api/auth/permissions/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
# ============================================================
# ROLE-PERMISSION ASSIGNMENT API TESTS
# ============================================================

class RolePermissionAssignmentAPITests(APITestCase):

    def setUp(self):
        self.manager = User.objects.create_user(
            email="rolepermissionmanager@example.com",
            full_name="Role Permission Manager",
            password="TestPassword@123",
        )

        self.manager_role = Role.objects.create(
            name="Role Permission Manager",
            description="Role with role management permission",
            is_system=False,
        )

        self.manage_permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manager_role,
            permission=self.manage_permission,
        )

        UserRole.objects.create(
            user=self.manager,
            role=self.manager_role,
        )

        self.target_role = Role.objects.create(
            name="Permission Assignment Target",
            description="Role for permission assignment",
            is_system=False,
        )

        self.target_permission = Permission.objects.create(
            codename="users.view",
            description="View users",
        )

        self.client.force_authenticate(
            user=self.manager
        )

    def test_assign_permission_to_role(self):

        response = self.client.post(
            f"/api/auth/roles/{self.target_role.id}/permissions/",
            {
                "permission_id": str(self.target_permission.id)
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            RolePermission.objects.filter(
                role=self.target_role,
                permission=self.target_permission,
            ).exists()
        )
# ============================================================
# DUPLICATE ROLE-PERMISSION ASSIGNMENT TESTS
# ============================================================

class DuplicateRolePermissionAssignmentAPITests(APITestCase):

    def setUp(self):
        self.manager = User.objects.create_user(
            email="duplicatepermissionmanager@example.com",
            full_name="Duplicate Permission Manager",
            password="TestPassword@123",
        )

        self.manager_role = Role.objects.create(
            name="Duplicate Permission Manager Role",
            description="Role with role management permission",
            is_system=False,
        )

        self.manage_permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manager_role,
            permission=self.manage_permission,
        )

        UserRole.objects.create(
            user=self.manager,
            role=self.manager_role,
        )

        self.target_role = Role.objects.create(
            name="Duplicate Permission Target",
            description="Role for duplicate permission testing",
            is_system=False,
        )

        self.target_permission = Permission.objects.create(
            codename="users.view",
            description="View users",
        )

        # First assignment
        RolePermission.objects.create(
            role=self.target_role,
            permission=self.target_permission,
        )

        self.client.force_authenticate(
            user=self.manager
        )

    def test_duplicate_permission_assignment(self):

        response = self.client.post(
            f"/api/auth/roles/{self.target_role.id}/permissions/",
            {
                "permission_id": str(self.target_permission.id)
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            RolePermission.objects.filter(
                role=self.target_role,
                permission=self.target_permission,
            ).count(),
            1,
        )
# ============================================================
# ROLE-PERMISSION ASSIGNMENT PERMISSION DENIAL TESTS
# ============================================================

class RolePermissionAssignmentPermissionAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="nopermissionassignment@example.com",
            full_name="No Permission Assignment User",
            password="TestPassword@123",
        )

        self.view_role = Role.objects.create(
            name="Role View Only Permission Assignment",
            description="Role with only roles.view permission",
            is_system=False,
        )

        self.view_permission = Permission.objects.create(
            codename="roles.view",
            description="View roles",
        )

        RolePermission.objects.create(
            role=self.view_role,
            permission=self.view_permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.view_role,
        )

        self.target_role = Role.objects.create(
            name="Permission Assignment Protected Role",
            description="Role that should not receive permission",
            is_system=False,
        )

        self.target_permission = Permission.objects.create(
            codename="users.view",
            description="View users",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_assign_permission_without_manage_permission(self):

        response = self.client.post(
            f"/api/auth/roles/{self.target_role.id}/permissions/",
            {
                "permission_id": str(self.target_permission.id)
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            RolePermission.objects.filter(
                role=self.target_role,
                permission=self.target_permission,
            ).exists()
        )
# ============================================================
# ROLE-PERMISSION REMOVAL API TESTS
# ============================================================

class RolePermissionRemovalAPITests(APITestCase):

    def setUp(self):
        self.manager = User.objects.create_user(
            email="rolepermissionremovemanager@example.com",
            full_name="Role Permission Remove Manager",
            password="TestPassword@123",
        )

        self.manager_role = Role.objects.create(
            name="Role Permission Remove Manager",
            description="Role with role management permission",
            is_system=False,
        )

        self.manage_permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manager_role,
            permission=self.manage_permission,
        )

        UserRole.objects.create(
            user=self.manager,
            role=self.manager_role,
        )

        self.target_role = Role.objects.create(
            name="Permission Removal Target",
            description="Role for permission removal",
            is_system=False,
        )

        self.target_permission = Permission.objects.create(
            codename="users.view",
            description="View users",
        )

        # Existing permission assignment
        RolePermission.objects.create(
            role=self.target_role,
            permission=self.target_permission,
        )

        self.client.force_authenticate(
            user=self.manager
        )

    def test_remove_permission_from_role(self):

        response = self.client.delete(
            f"/api/auth/roles/{self.target_role.id}/permissions/"
            f"{self.target_permission.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            RolePermission.objects.filter(
                role=self.target_role,
                permission=self.target_permission,
            ).exists()
        )
# ============================================================
# ROLE-PERMISSION REMOVAL PERMISSION DENIAL TESTS
# ============================================================

class RolePermissionRemovalPermissionAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="nopermissionremove@example.com",
            full_name="No Permission Remove User",
            password="TestPassword@123",
        )

        self.view_role = Role.objects.create(
            name="Role View Only Permission Removal",
            description="Role with only roles.view permission",
            is_system=False,
        )

        self.view_permission = Permission.objects.create(
            codename="roles.view",
            description="View roles",
        )

        RolePermission.objects.create(
            role=self.view_role,
            permission=self.view_permission,
        )

        UserRole.objects.create(
            user=self.user,
            role=self.view_role,
        )

        self.target_role = Role.objects.create(
            name="Permission Removal Protected Role",
            description="Role whose permission should not be removed",
            is_system=False,
        )

        self.target_permission = Permission.objects.create(
            codename="users.view",
            description="View users",
        )

        # Existing permission assignment
        RolePermission.objects.create(
            role=self.target_role,
            permission=self.target_permission,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_remove_permission_without_manage_permission(self):

        response = self.client.delete(
            f"/api/auth/roles/{self.target_role.id}/permissions/"
            f"{self.target_permission.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            RolePermission.objects.filter(
                role=self.target_role,
                permission=self.target_permission,
            ).exists()
        )
# ============================================================
# SYSTEM ROLE PERMISSION ASSIGNMENT PROTECTION TESTS
# ============================================================

class SystemRolePermissionAssignmentAPITests(APITestCase):

    def setUp(self):
        self.manager = User.objects.create_user(
            email="systempermissionmanager@example.com",
            full_name="System Permission Manager",
            password="TestPassword@123",
        )

        self.manager_role = Role.objects.create(
            name="System Permission Manager Role",
            description="Role with role management permission",
            is_system=False,
        )

        self.manage_permission = Permission.objects.create(
            codename="roles.manage",
            description="Manage roles",
        )

        RolePermission.objects.create(
            role=self.manager_role,
            permission=self.manage_permission,
        )

        UserRole.objects.create(
            user=self.manager,
            role=self.manager_role,
        )

        self.system_role = Role.objects.create(
            name="Protected System Permission Role",
            description="System role whose permissions are protected",
            is_system=True,
        )

        self.target_permission = Permission.objects.create(
            codename="users.view",
            description="View users",
        )

        self.client.force_authenticate(
            user=self.manager
        )

    def test_assign_permission_to_system_role(self):

        response = self.client.post(
            f"/api/auth/roles/{self.system_role.id}/permissions/",
            {
                "permission_id": str(self.target_permission.id)
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            RolePermission.objects.filter(
                role=self.system_role,
                permission=self.target_permission,
            ).exists()
        )