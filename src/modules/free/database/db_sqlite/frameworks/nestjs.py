"""NestJS framework plugin for the Db Sqlite module."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin

logger = logging.getLogger(__name__)

_NPM_DEPENDENCIES: Dict[str, str] = {
    "better-sqlite3": "^12.5.0",
}

_NPM_DEV_DEPENDENCIES: Dict[str, str] = {
    "@types/better-sqlite3": "^7.6.13",
}


class NestJSPlugin(FrameworkPlugin):
    """Plugin exposing NestJS-specific integrations for Db Sqlite."""

    @property
    def name(self) -> str:
        return "nestjs"

    @property
    def language(self) -> str:
        return "typescript"

    @property
    def display_name(self) -> str:
        return "NestJS"

    def get_template_mappings(self) -> Dict[str, str]:
        return {
            "service": "templates/variants/nestjs/db_sqlite.service.ts.j2",
            "controller": "templates/variants/nestjs/db_sqlite.controller.ts.j2",
            "module": "templates/variants/nestjs/db_sqlite.module.ts.j2",
            "configuration": "templates/variants/nestjs/db_sqlite.configuration.ts.j2",
            "health_controller": "templates/variants/nestjs/db_sqlite.health.controller.ts.j2",
            "health_module": "templates/variants/nestjs/db_sqlite.health.module.ts.j2",
            "integration_tests": "templates/tests/integration/db_sqlite.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/database/db_sqlite/db-sqlite/db-sqlite.service.ts",
            "controller": "src/modules/free/database/db_sqlite/db-sqlite/db-sqlite.controller.ts",
            "module": "src/modules/free/database/db_sqlite/db-sqlite/db-sqlite.module.ts",
            "configuration": "src/modules/free/database/db_sqlite/db-sqlite/db-sqlite.configuration.ts",
            "health_controller": "src/health/db-sqlite-health.controller.ts",
            "health_module": "src/health/db-sqlite-health.module.ts",
            "integration_tests": "tests/modules/integration/database/db_sqlite.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "module_kebab": base_context.get("module_kebab"),
            "vendor_configuration_relative": base_context.get(
                "rapidkit_vendor_configuration_relative"
            ),
            "configuration_output_relative": base_context.get("nest_configuration_relative"),
            "health_controller_relative": base_context.get("nest_health_controller_relative"),
            "health_module_relative": base_context.get("nest_health_module_relative"),
            "integration_test_relative": base_context.get("nest_test_relative"),
        }

    def validate_requirements(self) -> list[str]:  # noqa: D401
        """NestJS templates do not impose runtime requirements for generation."""

        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "database" / "db_sqlite"
        module_root.mkdir(parents=True, exist_ok=True)
        (module_root / "db-sqlite").mkdir(parents=True, exist_ok=True)
        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)
        (output_dir / "nestjs").mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "database").mkdir(
            parents=True, exist_ok=True
        )
        self._ensure_package_dependencies(output_dir / "package.json")

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: D401, ARG002
        """Re-run dependency enforcement after template rendering completes."""

        self._ensure_package_dependencies(output_dir / "package.json")

    def get_dependencies(self) -> list[str]:
        return ["@nestjs/common", "@nestjs/config", "better-sqlite3"]

    def get_dev_dependencies(self) -> list[str]:
        return ["@types/node"]

    def _ensure_package_dependencies(self, package_candidate: Path) -> None:
        package_path = self._locate_package_json(package_candidate)
        if package_path is None:
            logger.warning("Db Sqlite module package.json not found near %s", package_candidate)
            return

        try:
            package_data = json.loads(package_path.read_text())
        except json.JSONDecodeError:
            logger.warning("Skipping Db Sqlite dependency injection; package.json is invalid JSON")
            return

        if not isinstance(package_data, dict):
            logger.warning("package.json is not a JSON object; skipping dependency injection")
            return

        dependencies = package_data.get("dependencies")
        dev_dependencies = package_data.get("devDependencies")

        updated = False
        if isinstance(dependencies, dict):
            for pkg, version in _NPM_DEPENDENCIES.items():
                current = dependencies.get(pkg)
                if current != version:
                    dependencies[pkg] = version
                    updated = True
        else:
            package_data["dependencies"] = dict(_NPM_DEPENDENCIES)
            updated = True

        if isinstance(dev_dependencies, dict):
            for pkg, version in _NPM_DEV_DEPENDENCIES.items():
                current = dev_dependencies.get(pkg)
                if current != version:
                    dev_dependencies[pkg] = version
                    updated = True
        else:
            package_data["devDependencies"] = dict(_NPM_DEV_DEPENDENCIES)
            updated = True

        if updated:
            package_path.write_text(json.dumps(package_data, indent=2) + "\n")
            logger.info("Ensured Db Sqlite module dependencies are pinned in package.json")

    def _locate_package_json(self, candidate: Path) -> Path | None:
        if candidate.is_file():
            return candidate

        for root in (candidate, *candidate.parents):
            package_file = root / "package.json"
            if package_file.exists():
                return package_file
        return None


class NestJSStandardPlugin(NestJSPlugin):
    """Alias plugin mapping nestjs.standard to the canonical NestJS implementation."""

    @property
    def name(self) -> str:  # noqa: D401 - alias returns base plugin
        return "nestjs.standard"

    @property
    def display_name(self) -> str:
        return "NestJS (standard kit)"


__all__ = ["NestJSPlugin", "NestJSStandardPlugin"]
