"""Role-Based Access Control (RBAC) implementation for RapidKit."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger("src.modules.free.auth.core.auth.rbac")


class PermissionLevel(Enum):
    """Permission levels for granular access control."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


_PERMISSION_LEVEL_ORDER = {
    PermissionLevel.READ: 1,
    PermissionLevel.WRITE: 2,
    PermissionLevel.DELETE: 3,
    PermissionLevel.ADMIN: 4,
}


@dataclass(frozen=True)
class Permission:
    """Individual permission with resource and action."""
    resource: str
    action: str
    level: PermissionLevel
    conditions: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        base = f"{self.resource}:{self.action}:{self.level.value}"
        if self.conditions:
            conditions_str = json.dumps(self.conditions, sort_keys=True)
            return f"{base}[{conditions_str}]"
        return base

    def __hash__(self) -> int:
        """Ensure permissions remain hashable even with condition payloads."""
        if self.conditions is None:
            conditions_repr = None
        else:
            try:
                conditions_repr = json.dumps(self.conditions, sort_keys=True)
            except TypeError:
                conditions_repr = repr(self.conditions)
        return hash((self.resource, self.action, self.level, conditions_repr))

    @classmethod
    def from_string(cls, permission_str: str) -> "Permission":
        """Parse permission from string format."""
        if "[" in permission_str and permission_str.endswith("]"):
            base_part, conditions_part = permission_str.split("[", 1)
            conditions_json = conditions_part.rstrip("]")
            conditions = json.loads(conditions_json)
        else:
            base_part = permission_str
            conditions = None

        parts = base_part.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid permission format: {permission_str}")

        resource, action, level_str = parts
        level = PermissionLevel(level_str)

        return cls(
            resource=resource,
            action=action,
            level=level,
            conditions=conditions
        )


@dataclass(frozen=True)
class Role:
    """Role containing multiple permissions."""
    name: str
    description: str
    permissions: Set[Permission]
    inherits_from: Optional[Set[str]] = None
    is_system: bool = False

    def has_permission(
        self,
        resource: str,
        action: str,
        level: PermissionLevel,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if role has specific permission."""
        for perm in self.permissions:
            if not self._matches_resource(perm.resource, resource):
                continue
            if not self._matches_action(perm.action, action):
                continue
            if not self._satisfies_level(perm.level, level):
                continue

            if perm.conditions:
                if context and self._evaluate_conditions(perm.conditions, context):
                    return True
                continue

            return True
        return False

    @staticmethod
    def _matches_resource(granted: str, required: str) -> bool:
        return granted == "*" or granted == required

    @staticmethod
    def _matches_action(granted: str, required: str) -> bool:
        return granted == "*" or granted == required

    @staticmethod
    def _satisfies_level(granted: PermissionLevel, required: PermissionLevel) -> bool:
        return _PERMISSION_LEVEL_ORDER[granted] >= _PERMISSION_LEVEL_ORDER[required]

    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate permission conditions against context."""
        for key, expected_value in conditions.items():
            if key not in context:
                return False

            actual_value = context[key]
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif actual_value != expected_value:
                return False

        return True


class RBACManager:
    """Role-Based Access Control Manager."""

    def __init__(self) -> None:
        self._roles: Dict[str, Role] = {}
        self._user_roles: Dict[str, Set[str]] = {}
        self._setup_default_roles()

    def _setup_default_roles(self) -> None:
        """Setup default system roles."""
        # Super Admin - full access
        super_admin_perms = {
            Permission("*", "*", PermissionLevel.ADMIN),
        }
        self.add_role(Role(
            name="super_admin",
            description="Super administrator with full system access",
            permissions=super_admin_perms,
            is_system=True
        ))

        # Admin - most access except system management
        admin_perms = {
            Permission("users", "*", PermissionLevel.ADMIN),
            Permission("roles", "read", PermissionLevel.READ),
            Permission("content", "*", PermissionLevel.ADMIN),
            Permission("settings", "*", PermissionLevel.WRITE),
        }
        self.add_role(Role(
            name="admin",
            description="Administrator with elevated privileges",
            permissions=admin_perms,
            is_system=True
        ))

        # Editor - content management
        editor_perms = {
            Permission("content", "*", PermissionLevel.WRITE),
            Permission("users", "read", PermissionLevel.READ),
        }
        self.add_role(Role(
            name="editor",
            description="Content editor with write access",
            permissions=editor_perms,
            is_system=True
        ))

        # Viewer - read-only access
        viewer_perms = {
            Permission("content", "read", PermissionLevel.READ),
            Permission("users", "read", PermissionLevel.READ),
        }
        self.add_role(Role(
            name="viewer",
            description="Read-only access to content",
            permissions=viewer_perms,
            is_system=True
        ))

        # User - basic authenticated user
        user_perms = {
            Permission("profile", "*", PermissionLevel.WRITE, {"owner": True}),
            Permission("content", "read", PermissionLevel.READ),
        }
        self.add_role(Role(
            name="user",
            description="Basic authenticated user",
            permissions=user_perms,
            is_system=True
        ))

    def add_role(self, role: Role) -> None:
        """Add a new role to the system."""
        self._roles[role.name] = role
        logger.info(f"Added role: {role.name}")

    def remove_role(self, role_name: str) -> None:
        """Remove a role from the system."""
        if role_name in self._roles:
            role = self._roles[role_name]
            if role.is_system:
                raise ValueError(f"Cannot remove system role: {role_name}")
            del self._roles[role_name]
            logger.info(f"Removed role: {role_name}")

    def get_role(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        return self._roles.get(role_name)

    def list_roles(self) -> List[Role]:
        """List all available roles."""
        return list(self._roles.values())

    def assign_role(self, user_id: str, role_name: str) -> None:
        """Assign role to user."""
        if role_name not in self._roles:
            raise ValueError(f"Role not found: {role_name}")

        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()

        self._user_roles[user_id].add(role_name)
        logger.info(f"Assigned role {role_name} to user {user_id}")

    def revoke_role(self, user_id: str, role_name: str) -> None:
        """Revoke role from user."""
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_name)
            logger.info(f"Revoked role {role_name} from user {user_id}")

    def get_user_roles(self, user_id: str) -> Set[str]:
        """Get all roles assigned to user."""
        return self._user_roles.get(user_id, set())

    def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        level: PermissionLevel,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has specific permission."""
        user_roles = self.get_user_roles(user_id)

        for role_name in user_roles:
            role = self._roles.get(role_name)
            if role and role.has_permission(resource, action, level, context):
                return True

        return False

    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for user based on their roles."""
        user_roles = self.get_user_roles(user_id)
        permissions: Set[Permission] = set()

        for role_name in user_roles:
            role = self._roles.get(role_name)
            if role:
                permissions.update(role.permissions)

        return permissions

    def create_custom_role(
        self,
        name: str,
        description: str,
        permissions: List[str],
        inherits_from: Optional[List[str]] = None
    ) -> Role:
        """Create a custom role from permission strings."""
        perm_objects = {Permission.from_string(p) for p in permissions}

        # Add inherited permissions
        if inherits_from:
            for parent_role_name in inherits_from:
                parent_role = self._roles.get(parent_role_name)
                if parent_role:
                    perm_objects.update(parent_role.permissions)

        role = Role(
            name=name,
            description=description,
            permissions=perm_objects,
            inherits_from=set(inherits_from) if inherits_from else None,
            is_system=False
        )

        self.add_role(role)
        return role


# Decorator for permission checking
def require_permission(
    resource: str,
    action: str,
    level: PermissionLevel,
    context_key: Optional[str] = None
):
    """Decorator to require specific permission for endpoint access."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would integrate with FastAPI dependency injection
            # For now, we'll just mark the function with permission requirements
            if not hasattr(func, '_required_permissions'):
                func._required_permissions = []

            func._required_permissions.append({
                'resource': resource,
                'action': action,
                'level': level,
                'context_key': context_key
            })

            return func(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    "Permission",
    "PermissionLevel",
    "Role",
    "RBACManager",
    "require_permission",
]
