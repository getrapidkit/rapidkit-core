"""Tests for JWT Advanced functionality."""

from unittest.mock import patch

import pytest

from modules.free.auth.core.generate import AuthCoreModuleGenerator

# Constants
JWT_PARTS_COUNT = 2  # JWT has 3 parts separated by 2 dots
EXPECTED_PERMISSIONS_COUNT = 3


class TestJWTAdvanced:
    """Test JWT Advanced Runtime."""

    @pytest.fixture
    def generator(self) -> AuthCoreModuleGenerator:
        return AuthCoreModuleGenerator()

    @pytest.fixture
    def rendered_module(self, generator, tmp_path):
        """Render the auth core module for testing."""
        config = generator.load_module_config()
        base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
        renderer = generator.create_renderer()

        generator.generate_vendor_files(config, tmp_path, renderer, base_context)
        generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)

        # Import the rendered modules
        import importlib.util
        import sys

        # Load core module
        vendor_root = tmp_path / ".rapidkit" / "vendor" / config["name"] / config["version"]
        core_path = vendor_root / base_context["rapidkit_vendor_python_relative"]

        spec = importlib.util.spec_from_file_location("modules.free.auth.core.auth.core", core_path)
        auth_core = importlib.util.module_from_spec(spec)
        sys.modules["modules.free.auth.core.auth.core"] = auth_core
        spec.loader.exec_module(auth_core)

        # Load JWT advanced module
        jwt_path = vendor_root / "src/modules/free/auth/core/auth/jwt_advanced.py"
        spec = importlib.util.spec_from_file_location(
            "modules.free.auth.core.auth.jwt_advanced", jwt_path
        )
        jwt_advanced = importlib.util.module_from_spec(spec)
        sys.modules["modules.free.auth.core.auth.jwt_advanced"] = jwt_advanced
        spec.loader.exec_module(jwt_advanced)

        # Load RBAC module
        rbac_path = vendor_root / "src/modules/free/auth/core/auth/rbac.py"
        spec = importlib.util.spec_from_file_location("modules.free.auth.core.auth.rbac", rbac_path)
        rbac = importlib.util.module_from_spec(spec)
        sys.modules["modules.free.auth.core.auth.rbac"] = rbac
        spec.loader.exec_module(rbac)

        return {"auth_core": auth_core, "jwt_advanced": jwt_advanced, "rbac": rbac}

    def test_jwt_claims_creation(self, rendered_module):
        """Test JWT claims creation and serialization."""
        jwt_advanced = rendered_module["jwt_advanced"]

        claims = jwt_advanced.JWTClaims(
            iss="test-issuer",
            sub="user-123",
            aud="test-audience",
            scopes=["read", "write"],
            roles=["admin"],
            tenant_id="tenant-1",
        )

        claims_dict = claims.to_dict()

        assert claims_dict["iss"] == "test-issuer"
        assert claims_dict["sub"] == "user-123"
        assert claims_dict["aud"] == "test-audience"
        assert claims_dict["scopes"] == ["read", "write"]
        assert claims_dict["roles"] == ["admin"]
        assert claims_dict["tenant_id"] == "tenant-1"

        # Test round-trip
        recreated = jwt_advanced.JWTClaims.from_dict(claims_dict)
        assert recreated == claims

    @patch.dict("os.environ", {"RAPIDKIT_AUTH_CORE_PEPPER": "test-pepper"})
    def test_jwt_advanced_runtime(self, rendered_module):
        """Test JWT Advanced Runtime operations."""
        auth_core = rendered_module["auth_core"]
        jwt_advanced = rendered_module["jwt_advanced"]

        settings = auth_core.load_settings()
        core_runtime = auth_core.AuthCoreRuntime(settings)
        jwt_runtime = jwt_advanced.JWTAdvancedRuntime(core_runtime)

        # Test access token issuance
        access_token = jwt_runtime.issue_access_token(
            subject="user-123",
            audience="api",
            scopes=["read", "write"],
            roles=["admin"],
            tenant_id="tenant-1",
        )

        assert isinstance(access_token, str)
        assert access_token.count(".") == JWT_PARTS_COUNT  # JWT format

        # Test token verification
        claims = jwt_runtime.verify_access_token(
            access_token, required_scopes=["read"], required_audience="api"
        )

        assert claims.sub == "user-123"
        assert claims.aud == "api"
        assert "read" in claims.scopes
        assert "admin" in claims.roles
        assert claims.tenant_id == "tenant-1"

        # Test refresh token
        refresh_token = jwt_runtime.issue_refresh_token(
            subject="user-123", session_id="session-456"
        )

        assert isinstance(refresh_token, str)

        # Test token revocation
        jwt_runtime.revoke_token(access_token)

        with pytest.raises(ValueError, match="revoked"):
            jwt_runtime.verify_access_token(access_token)

    def test_rbac_manager(self, rendered_module):
        """Test RBAC Manager functionality."""
        rbac = rendered_module["rbac"]

        manager = rbac.RBACManager()

        # Test default roles exist
        assert manager.get_role("super_admin") is not None
        assert manager.get_role("admin") is not None
        assert manager.get_role("user") is not None

        # Test role assignment
        manager.assign_role("user-123", "admin")
        user_roles = manager.get_user_roles("user-123")
        assert "admin" in user_roles

        # Test permission checking
        has_permission = manager.check_permission(
            "user-123", "users", "read", rbac.PermissionLevel.READ
        )
        assert has_permission is True

        # Test custom role creation
        custom_role = manager.create_custom_role(
            name="content_manager",
            description="Manages content",
            permissions=["content:create:write", "content:edit:write", "content:delete:delete"],
        )

        assert custom_role.name == "content_manager"
        assert len(custom_role.permissions) == EXPECTED_PERMISSIONS_COUNT

        # Test role revocation
        manager.revoke_role("user-123", "admin")
        user_roles = manager.get_user_roles("user-123")
        assert "admin" not in user_roles

    def test_permission_parsing(self, rendered_module):
        """Test permission string parsing."""
        rbac = rendered_module["rbac"]

        # Simple permission
        perm = rbac.Permission.from_string("users:read:read")
        assert perm.resource == "users"
        assert perm.action == "read"
        assert perm.level == rbac.PermissionLevel.READ
        assert perm.conditions is None

        # Permission with conditions
        perm_with_conditions = rbac.Permission.from_string(
            'content:edit:write[{"owner": true, "status": ["draft", "review"]}]'
        )
        assert perm_with_conditions.resource == "content"
        assert perm_with_conditions.action == "edit"
        assert perm_with_conditions.level == rbac.PermissionLevel.WRITE
        assert perm_with_conditions.conditions == {"owner": True, "status": ["draft", "review"]}

        # Test round-trip
        perm_str = str(perm_with_conditions)
        recreated = rbac.Permission.from_string(perm_str)
        assert recreated == perm_with_conditions
