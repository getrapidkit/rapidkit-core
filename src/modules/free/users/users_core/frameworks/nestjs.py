"""NestJS framework plugin for Users Core."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import ensure_health_package


class NestJSPlugin(FrameworkPlugin):
    """Generate NestJS-ready Users Core runtime."""

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
            "users_index": "templates/variants/nestjs/index.ts.j2",
            "users_service": "templates/variants/nestjs/users-core.service.ts.j2",
            "users_controller": "templates/variants/nestjs/users_core.controller.ts.j2",
            "users_module": "templates/variants/nestjs/users_core.module.ts.j2",
            "users_configuration": "templates/variants/nestjs/users_core.configuration.ts.j2",
            "users_health_controller": "templates/variants/nestjs/users_core.health.controller.ts.j2",
            "users_metadata_controller": "templates/variants/nestjs/users_core.metadata.controller.ts.j2",
            "users_health_module": "templates/variants/nestjs/users_core.health.module.ts.j2",
            "integration_test": "templates/tests/integration/test_users_core_integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            # Canonical NestJS layout: avoid a nested kebab-case folder under the module base.
            # (The installer flattens nested duplicates like '<module>/<module-kebab>/*'.)
            "users_index": "src/modules/free/users/users_core/index.ts",
            "users_service": "src/modules/free/users/users_core/users-core.service.ts",
            "users_controller": "src/modules/free/users/users_core/users-core.controller.ts",
            "users_module": "src/modules/free/users/users_core/users-core.module.ts",
            "users_configuration": "src/modules/free/users/users_core/users-core.configuration.ts",
            "users_health_controller": "src/health/users-core-health.controller.ts",
            "users_metadata_controller": "src/modules/free/users/users_core/core/users/metadata.controller.ts",
            "users_health_module": "src/health/users-core-health.module.ts",
            "integration_test": "tests/modules/free/users/users_core/users-core.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "configuration_relative": base_context.get("nest_configuration_relative"),
            "health_controller_relative": base_context.get("nest_health_controller_relative"),
            "health_module_relative": base_context.get("nest_health_module_relative"),
            "integration_test_relative": base_context.get("nest_test_relative"),
        }

    def validate_requirements(self) -> List[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "users" / "users_core"
        base.mkdir(parents=True, exist_ok=True)
        (base / "core" / "users").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "free" / "users" / "users_core").mkdir(
            parents=True, exist_ok=True
        )

        # Best-effort: materialise vendor-backed health shim (`src/health/users_core.py`)
        # so the canonical health registry can import `register_users_core_health`.
        from modules.shared.utils.health import ensure_vendor_health_shim
        from modules.shared.utils.health_specs import build_standard_health_spec

        with suppress(RuntimeError, OSError):
            spec = build_standard_health_spec(Path(__file__).resolve().parents[1])
            ensure_vendor_health_shim(output_dir, spec=spec)

        ensure_health_package(
            output_dir,
            extra_imports=[
                (
                    "src.health.users_core",
                    "register_users_core_health",
                ),
            ],
        )

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
