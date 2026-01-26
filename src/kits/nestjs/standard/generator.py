"""NestJS standard kit generator."""

from pathlib import Path
from typing import Any, Dict, List

from core.engine.generator import BaseKitGenerator
from kits.shared import get_settings_vendor_metadata


class NestJSStandardGenerator(BaseKitGenerator):
    """Generator for the NestJS standard kit."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.selected_modules: List[Dict[str, Any]] = []
        self._context_variables: Dict[str, Any] = {
            "database_type": "none",
            "include_caching": False,
            "include_monitoring": False,
            "include_logging": True,
            "include_testing": True,
            "include_docs": True,
            "docker_support": True,
            "auth_type": "none",
            "package_manager": "npm",
        }

    def _validate_variables(self, variables: Dict[str, Any]) -> None:
        required_vars = ["project_name"]

        for var in required_vars:
            if var not in variables or not variables[var]:
                raise ValueError(f"Variable '{var}' is required")

        project_name = variables["project_name"]
        normalized = project_name.replace("-", "").replace("_", "")
        if not normalized.isalnum():
            raise ValueError(
                "Project name should contain only letters, numbers, hyphens, and underscores"
            )

        package_manager = variables.get("package_manager")
        if package_manager and package_manager not in {"npm", "yarn", "pnpm"}:
            raise ValueError("package_manager must be one of: npm, yarn, pnpm")

        if variables.get("database_type") == "sqlite" and variables.get("auth_type") == "oauth2":
            raise ValueError(
                "SQLite is not recommended for OAuth2 features. Consider using PostgreSQL or MySQL."
            )

    def _resolve_modules(self, variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        modules: List[Dict[str, Any]] = []

        if variables.get("auth_type") != "none":
            modules.append({"name": "auth", "tier": "free", "version": "latest", "required": True})

        database_type = variables.get("database_type")
        if database_type and database_type != "none":
            db_module = f"db_{database_type}"
            modules.append(
                {"name": db_module, "tier": "free", "version": "latest", "required": True}
            )

        if variables.get("include_monitoring"):
            modules.append(
                {"name": "monitoring", "tier": "free", "version": "latest", "required": False}
            )

        if variables.get("include_caching"):
            modules.append(
                {"name": "redis", "tier": "free", "version": "latest", "required": False}
            )

        if variables.get("include_logging"):
            modules.append(
                {"name": "logging", "tier": "free", "version": "latest", "required": False}
            )

        return modules

    def extra_context(self) -> Dict[str, Any]:
        variables = self._context_variables

        def _as_bool(value: Any, default: bool = False) -> bool:
            if isinstance(value, bool):
                return value
            if value is None:
                return default
            if isinstance(value, str):
                return value.strip().lower() in {"true", "1", "yes", "on"}
            return bool(value)

        database_type = str(variables.get("database_type", "none")).lower()
        auth_type = str(variables.get("auth_type", "none")).lower()
        package_manager_raw = variables.get("package_manager", "npm")
        package_manager = str(package_manager_raw).lower() if package_manager_raw else "npm"

        context = {
            "has_postgres": database_type == "postgresql",
            "has_mysql": database_type == "mysql",
            "has_sqlite": database_type == "sqlite",
            "has_mongodb": database_type == "mongodb",
            "has_redis": _as_bool(variables.get("include_caching"), False),
            "has_monitoring": _as_bool(variables.get("include_monitoring"), False),
            "has_logging": _as_bool(variables.get("include_logging"), False),
            "has_testing": _as_bool(variables.get("include_testing"), True),
            "has_docs": _as_bool(variables.get("include_docs"), True),
            "has_docker": _as_bool(variables.get("docker_support"), True),
            "has_ci": _as_bool(variables.get("include_ci"), True),
            "package_manager": package_manager,
            "package_manager_command": "pnpm" if package_manager == "pnpm" else package_manager,
            "auth_jwt": auth_type == "jwt",
            "auth_oauth2": auth_type == "oauth2",
            "selected_modules": self.selected_modules,
            "runtime": "node",
            "node_version": str(variables.get("node_version", "20.19.6")),
        }
        vendor_meta = get_settings_vendor_metadata()
        context.update(
            rapidkit_vendor_root=vendor_meta["vendor_root"],
            rapidkit_vendor_module=vendor_meta["module_name"],
            rapidkit_vendor_version=vendor_meta["version"],
        )
        return context

    def generate(self, output_path: Path, variables: Dict[str, Any]) -> List[str]:
        normalized_variables = self._validate_and_normalize_variables(variables)
        self._validate_variables(normalized_variables)
        self.selected_modules = self._resolve_modules(normalized_variables)
        self._context_variables = normalized_variables
        return super().generate(output_path, normalized_variables)
