from django.core.management.base import BaseCommand

from users.models import Permission, Role, RolePermission


class Command(BaseCommand):
    help = "Create Sentra default roles and permissions"

    def handle(self, *args, **options):
        permissions = [
            ("users.view", "View users"),
            ("users.create", "Create users"),
            ("users.edit", "Edit users"),
            ("users.delete", "Delete users"),
            ("roles.view", "View roles"),
            ("roles.manage", "Manage roles"),
            ("permissions.view", "View permissions"),
            ("audit.view", "View audit logs"),
        ]

        permission_objects = {}

        for codename, description in permissions:
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={"description": description},
            )
            permission_objects[codename] = permission

        roles = [
            ("Admin", "Full system access"),
            ("Manager", "Manage users and roles"),
            ("Viewer", "Read-only access"),
        ]

        role_objects = {}

        for name, description in roles:
            role, _ = Role.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "is_system": True,
                },
            )
            role_objects[name] = role

        role_permissions = {
            "Admin": [
                "users.view",
                "users.create",
                "users.edit",
                "users.delete",
                "roles.view",
                "roles.manage",
                "permissions.view",
                "audit.view",
            ],
            "Manager": [
                "users.view",
                "users.create",
                "users.edit",
                "users.delete",
                "roles.view",
                "roles.manage",
            ],
            "Viewer": [
                "users.view",
                "roles.view",
                "permissions.view",
                "audit.view",
            ],
        }

        for role_name, permission_names in role_permissions.items():
            role = role_objects[role_name]

            for permission_name in permission_names:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission_objects[permission_name],
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Default roles, permissions, and role-permissions created successfully."
            )
        )