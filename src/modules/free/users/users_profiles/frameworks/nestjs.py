"""NestJS framework plugin for Users Profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin


class NestJSPlugin(FrameworkPlugin):
    """Generate NestJS-ready Users Profiles runtime."""

    @property
    def name(self) -> str:  # noqa: D401 - short alias
        return "nestjs"

    @property
    def language(self) -> str:  # noqa: D401 - short alias
        return "typescript"

    @property
    def display_name(self) -> str:  # noqa: D401 - short alias
        return "NestJS"

    def get_template_mappings(self) -> Dict[str, str]:
        return {
            "profiles_index": "templates/variants/nestjs/index.ts.j2",
            "profiles_service": "templates/variants/nestjs/users_profiles.service.ts.j2",
            "profiles_controller": "templates/variants/nestjs/users_profiles.controller.ts.j2",
            "profiles_module": "templates/variants/nestjs/users_profiles.module.ts.j2",
            "profiles_configuration": "templates/variants/nestjs/users_profiles.configuration.ts.j2",
            "profiles_health_controller": "templates/variants/nestjs/users_profiles.health.controller.ts.j2",
            "profiles_health_module": "templates/variants/nestjs/users_profiles.health.module.ts.j2",
            "integration_test": "templates/tests/integration/test_users_profiles_integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "profiles_index": "src/modules/free/users/users_profiles/index.ts",
            "profiles_service": "src/modules/free/users/users_profiles/users-profiles.service.ts",
            "profiles_controller": "src/modules/free/users/users_profiles/users-profiles.controller.ts",
            "profiles_module": "src/modules/free/users/users_profiles/users-profiles.module.ts",
            "profiles_configuration": "src/modules/free/users/users_profiles/users-profiles.configuration.ts",
            "profiles_health_controller": "src/health/users_profiles-health.controller.ts",
            "profiles_health_module": "src/health/users_profiles-health.module.ts",
            "integration_test": "tests/modules/integration/users/users_profiles.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "configuration_relative": base_context.get("nest_configuration_relative"),
            "health_controller_relative": base_context.get("nest_health_controller_relative"),
            "health_module_relative": base_context.get("nest_health_module_relative"),
            "integration_test_relative": base_context.get("nest_test_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "users" / "users_profiles"
        base.mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "users").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: ARG002
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "nestjs": "https://docs.nestjs.com/",
        }

    def get_dependencies(self) -> List[str]:
        return [
            "@nestjs/common@^10.0.0",
            "@nestjs/config@^3.0.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "@types/node@^20.0.0",
            "jest@^29.0.0",
            "@nestjs/testing@^10.0.0",
        ]
