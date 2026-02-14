"""FastAPI Standard kit generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from core.engine.generator import BaseKitGenerator


class FastAPIStandardGenerator(BaseKitGenerator):
    """Minimal generator that delegates capabilities to RapidKit modules."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.selected_modules: List[Dict[str, Any]] = []
        self._context_variables: Dict[str, Any] = {}

    @property
    def required_modules(self) -> List[Dict[str, Any]]:
        """Return modules that should always ship with the kit."""

        return [
            {"name": "middleware", "tier": "free", "version": "latest", "required": True},
            {"name": "shared_utils", "tier": "free", "version": "latest", "required": True},
            {"name": "domain_user_profile", "tier": "free", "version": "latest", "required": True},
            {
                "name": "infrastructure_user_profile",
                "tier": "free",
                "version": "latest",
                "required": True,
            },
            {
                "name": "application_user_profile",
                "tier": "free",
                "version": "latest",
                "required": True,
            },
            {"name": "presentation_http", "tier": "free", "version": "latest", "required": True},
        ]

    def _validate_variables(self, variables: Dict[str, Any]) -> None:
        project_name = variables.get("project_name")
        if not project_name:
            raise ValueError("Variable 'project_name' is required")
        normalized = project_name.replace("-", "_")
        if not normalized.isidentifier():
            raise ValueError(
                "Project name should start with a letter and contain only alphanumeric characters or underscores"
            )

    def _resolve_modules(self, variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine which modules should be installed for the kit."""

        modules = list(self.required_modules)

        def ensure_module(name: str, *, required: bool) -> None:
            for module in modules:
                if module["name"] == name:
                    if required:
                        module["required"] = True
                    return
            modules.append(
                {
                    "name": name,
                    "tier": "free",
                    "version": "latest",
                    "required": required,
                }
            )

        if variables.get("install_settings", True):
            ensure_module("settings", required=True)

        if variables.get("install_logging", True):
            ensure_module("logging", required=True)

        if variables.get("install_deployment", True):
            ensure_module("deployment", required=False)

        if variables.get("enable_tracing", False):
            ensure_module("tracing", required=False)

        if variables.get("enable_postgres", False):
            ensure_module("db_postgres", required=True)
        elif variables.get("enable_sqlite", True):
            ensure_module("db_sqlite", required=False)

        if variables.get("enable_monitoring", False):
            ensure_module("monitoring", required=False)

        if variables.get("enable_redis", False):
            ensure_module("redis", required=False)

        if variables.get("enable_docs", True):
            ensure_module("openapi_docs", required=False)

        auth_strategy = str(variables.get("auth_strategy", "none")).lower()
        if auth_strategy != "none":
            ensure_module("security", required=True)
            ensure_module("auth", required=True)

        return modules

    def extra_context(self) -> Dict[str, Any]:
        auth_strategy = str(self._context_variables.get("auth_strategy", "none")).lower()

        modules = {module["name"] for module in self.selected_modules}

        flags = {
            "has_postgres": "db_postgres" in modules,
            "has_sqlite": "db_sqlite" in modules,
            "has_redis": "redis" in modules,
            "has_monitoring": "monitoring" in modules,
            "has_logging": "logging" in modules,
            "has_settings": "settings" in modules,
            "has_deployment": "deployment" in modules,
            "has_tracing": "tracing" in modules,
            "has_docs": "openapi_docs" in modules,
            "has_testing": bool(self._context_variables.get("enable_testing", True)),
            "has_docker": bool(self._context_variables.get("enable_docker", True)),
            "has_ci": bool(self._context_variables.get("enable_ci", True)),
            "auth_jwt": auth_strategy == "jwt",
            "auth_oauth2": auth_strategy == "oauth2",
            "auth_basic": auth_strategy == "basic",
            "selected_modules": self.selected_modules,
            "python_version": str(self._context_variables.get("python_version", "3.10")),
            "runtime": "python",
        }

        return flags

    def generate(self, output_path: Path, variables: Dict[str, Any]) -> List[str]:
        normalized_variables = self._validate_and_normalize_variables(variables)
        self._validate_variables(normalized_variables)
        self.selected_modules = self._resolve_modules(normalized_variables)
        self._context_variables = normalized_variables
        return super().generate(output_path, normalized_variables)
