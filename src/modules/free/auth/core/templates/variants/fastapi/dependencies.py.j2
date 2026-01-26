"""FastAPI dependency providers for Auth Core with advanced features."""

from __future__ import annotations

import logging
from functools import lru_cache
from importlib import import_module
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.modules.free.auth.core.auth.core import AuthCoreRuntime, AuthCoreSettings, load_settings
from src.modules.free.auth.core.auth.jwt_advanced import JWTAdvancedRuntime, JWTClaims
from src.modules.free.auth.core.auth.rbac import RBACManager, PermissionLevel

logger = logging.getLogger("src.modules.free.auth.core.auth.dependencies")

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


def _resolve_settings_module() -> Any:
    """Resolve project settings module."""
    candidates = (
        "src.modules.free.essentials.settings.settings",
        "src.settings",
    )
    for candidate in candidates:
        try:
            return import_module(candidate)
        except (ModuleNotFoundError, ImportError):
            continue
    return None


def _get_project_settings_instance() -> Any:
    """Get project settings instance."""
    module = _resolve_settings_module()
    if module is None:
        return None

    provider = getattr(module, "get_settings", None)
    if callable(provider):
        try:
            return provider()
        except Exception:
            return None

    settings_cls = getattr(module, "Settings", None)
    if settings_cls is None:
        return None

    try:
        return settings_cls()
    except Exception:
        return None


@lru_cache()
def get_auth_core_settings() -> AuthCoreSettings:
    """Get Auth Core settings with project overrides."""
    overrides = {}
    project_settings = _get_project_settings_instance()

    if project_settings is not None:
        auth_attrs = [
            "auth_pepper_env", "auth_token_ttl", "auth_iterations",
            "auth_hash_name", "auth_salt_bytes", "auth_token_bytes",
            "auth_issuer"
        ]

        for attr in auth_attrs:
            value = getattr(project_settings, attr, None)
            if value is not None:
                # Convert to expected key format
                key = attr.replace("auth_", "").replace("_env", "_env")
                if key == "token_ttl":
                    key = "token_ttl_seconds"
                overrides[key] = value

    return load_settings(overrides)


@lru_cache()
def get_auth_core_runtime() -> AuthCoreRuntime:
    """Get Auth Core runtime instance."""
    settings = get_auth_core_settings()
    return AuthCoreRuntime(settings)


@lru_cache()
def get_jwt_advanced_runtime() -> JWTAdvancedRuntime:
    """Get JWT Advanced runtime instance."""
    core_runtime = get_auth_core_runtime()
    return JWTAdvancedRuntime(core_runtime)


@lru_cache()
def get_rbac_manager() -> RBACManager:
    """Get RBAC manager instance."""
    return RBACManager()


async def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Extract and validate Bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


async def get_current_user_claims(
    token: str = Depends(get_current_user_token),
    jwt_runtime: JWTAdvancedRuntime = Depends(get_jwt_advanced_runtime)
) -> JWTClaims:
    """Verify token and return claims."""
    try:
        return jwt_runtime.verify_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    claims: JWTClaims = Depends(get_current_user_claims)
) -> str:
    """Get current user ID from token claims."""
    if not claims.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim"
        )
    return claims.sub


async def get_current_user_scopes(
    claims: JWTClaims = Depends(get_current_user_claims)
) -> List[str]:
    """Get current user scopes from token."""
    return claims.scopes or []


async def get_current_user_roles(
    claims: JWTClaims = Depends(get_current_user_claims)
) -> List[str]:
    """Get current user roles from token."""
    return claims.roles or []


def require_scopes(*required_scopes: str):
    """Dependency factory to require specific scopes."""
    async def check_scopes(
        user_scopes: List[str] = Depends(get_current_user_scopes)
    ) -> None:
        user_scope_set = set(user_scopes)
        required_scope_set = set(required_scopes)

        if not required_scope_set.issubset(user_scope_set):
            missing_scopes = required_scope_set - user_scope_set
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scopes. Missing: {', '.join(missing_scopes)}"
            )

    return check_scopes


def require_roles(*required_roles: str):
    """Dependency factory to require specific roles."""
    async def check_roles(
        user_roles: List[str] = Depends(get_current_user_roles)
    ) -> None:
        user_role_set = set(user_roles)
        required_role_set = set(required_roles)

        if not required_role_set.intersection(user_role_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient roles. Required one of: {', '.join(required_roles)}"
            )

    return check_roles


def require_permission(
    resource: str,
    action: str,
    level: PermissionLevel,
    context_key: Optional[str] = None
):
    """Dependency factory to require specific permission."""
    async def check_permission(
        request: Request,
        user_id: str = Depends(get_current_user_id),
        rbac: RBACManager = Depends(get_rbac_manager)
    ) -> None:
        context = {}

        # Build context from request if context_key provided
        if context_key:
            if context_key in request.path_params:
                context[context_key] = request.path_params[context_key]
            elif hasattr(request.state, context_key):
                context[context_key] = getattr(request.state, context_key)

        # Add user context
        context["user_id"] = user_id

        if not rbac.check_permission(user_id, resource, action, level, context):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {resource}:{action}:{level.value}"
            )

    return check_permission


def optional_auth():
    """Optional authentication dependency."""
    async def get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        jwt_runtime: JWTAdvancedRuntime = Depends(get_jwt_advanced_runtime)
    ) -> Optional[JWTClaims]:
        if not credentials:
            return None

        try:
            return jwt_runtime.verify_access_token(credentials.credentials)
        except ValueError:
            return None

    return get_optional_user


# Backward compatibility aliases
def get_auth_core_dependency() -> AuthCoreRuntime:
    """Backward compatibility alias."""
    return get_auth_core_runtime()


__all__ = [
    "get_auth_core_settings",
    "get_auth_core_runtime",
    "get_jwt_advanced_runtime",
    "get_rbac_manager",
    "get_current_user_token",
    "get_current_user_claims",
    "get_current_user_id",
    "get_current_user_scopes",
    "get_current_user_roles",
    "require_scopes",
    "require_roles",
    "require_permission",
    "optional_auth",
    "get_auth_core_dependency",  # backward compatibility
]
