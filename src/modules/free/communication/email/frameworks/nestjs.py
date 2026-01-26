# pyright: reportMissingImports=false
"""NestJS framework plugin for the Email module."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)
logger = logging.getLogger(__name__)


_NPM_DEPENDENCIES: Dict[str, str] = {
    "nodemailer": "^6.9.0",
}

_NPM_DEV_DEPENDENCIES: Dict[str, str] = {
    "@types/nodemailer": "^6.4.0",
}


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS wrappers around the Email runtime."""

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
            "service": "templates/variants/nestjs/email.service.ts.j2",
            "controller": "templates/variants/nestjs/email.controller.ts.j2",
            "module": "templates/variants/nestjs/email.module.ts.j2",
            "configuration": "templates/variants/nestjs/email.configuration.ts.j2",
            "health": "templates/variants/nestjs/email.health.ts.j2",
            "integration_test": "templates/tests/integration/email.integration.spec.ts.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "service": "src/modules/free/communication/email/email.service.ts",
            "controller": "src/modules/free/communication/email/email.controller.ts",
            "module": "src/modules/free/communication/email/email.module.ts",
            "configuration": "src/modules/free/communication/email/email.configuration.ts",
            "health": "src/modules/free/communication/email/email.health.ts",
            "integration_test": "tests/modules/integration/communication/email.integration.spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "nestjs",
            "framework_display_name": "NestJS",
            "language": "typescript",
            "module_kebab": "email",
            "module_class_name": "Email",
        }

    def validate_requirements(self) -> list[str]:
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        base = output_dir / "src" / "modules" / "free" / "communication" / "email"
        base.mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "communication").mkdir(
            parents=True, exist_ok=True
        )

    def post_generation_hook(self, output_dir: Path) -> None:  # noqa: D401, ARG002
        """No-op hook.

        This module intentionally avoids mutating Node package manifests during install.
        """
        return

    def _ensure_package_dependencies(self, package_candidate: Path) -> None:
        package_path = self._locate_package_json(package_candidate)
        if package_path is None:
            logger.warning("Email module package.json not found near %s", package_candidate)
            return

        try:
            package_data = json.loads(package_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Skipping Email dependency injection; package.json is invalid JSON")
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
            package_path.write_text(json.dumps(package_data, indent=2) + "\n", encoding="utf-8")
            logger.info("Ensured Email module dependencies are pinned in package.json")

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
