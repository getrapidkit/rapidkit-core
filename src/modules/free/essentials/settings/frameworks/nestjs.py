# pyright: reportMissingImports=false

"""NestJS framework plugin for settings module code generation."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess  # nosec
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health_specs import build_standard_health_spec

MODULE_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SHIM_SPEC = build_standard_health_spec(MODULE_ROOT)

# Minimum Node.js version required for NestJS
MIN_NODE_VERSION = 16

logger = logging.getLogger(__name__)  # pylint: disable=E1101

_DEFAULT_TSCONFIG: Dict[str, Any] = {
    "compilerOptions": {
        "module": "commonjs",
        "declaration": True,
        "removeComments": True,
        "emitDecoratorMetadata": True,
        "experimentalDecorators": True,
        "allowSyntheticDefaultImports": True,
        "target": "ES2020",
        "sourceMap": True,
        "outDir": "./dist",
        "baseUrl": "./",
        "incremental": True,
        "skipLibCheck": True,
        "strictNullChecks": False,
        "noImplicitAny": False,
        "strictBindCallApply": False,
        "forceConsistentCasingInFileNames": False,
        "noFallthroughCasesInSwitch": False,
    }
}

_DEFAULT_PACKAGE_JSON: Dict[str, Any] = {
    "name": "nestjs-app",
    "version": "1.0.0",
    "description": "A NestJS application with settings management",
    "author": "",
    "private": True,
    "license": "UNLICENSED",
    "scripts": {
        "build": "nest build",
        "format": 'prettier --write "src/**/*.ts" "test/**/*.ts"',
        "start": "nest start",
        "start:dev": "nest start --watch",
        "start:debug": "nest start --debug --watch",
        "start:prod": "node dist/main",
        "lint": 'eslint "{src,apps,libs,test}/**/*.ts" --fix',
        "test": "jest",
        "test:watch": "jest --watch",
        "test:cov": "jest --coverage",
        "test:debug": "node --inspect-brk -r tsconfig-paths/register -r ts-node/register node_modules/.bin/jest --runInBand",
        "test:e2e": "jest --config ./test/jest-e2e.json",
    },
    "dependencies": {
        "@nestjs/common": "^11.1.6",
        "@nestjs/core": "^11.1.6",
        "@nestjs/platform-express": "^11.1.6",
        "@nestjs/config": "^4.0.2",
        "reflect-metadata": "^0.1.13",
        "rxjs": "^7.8.1",
        "class-validator": "^0.14.0",
        "class-transformer": "^0.5.1",
    },
    "devDependencies": {
        "@nestjs/cli": "^11.0.10",
        "@nestjs/schematics": "^11.0.10",
        "@nestjs/testing": "^11.1.6",
        "@types/express": "^4.17.17",
        "@types/node": "^20.0.0",
        "@types/jest": "^29.5.0",
        "@types/supertest": "^2.0.12",
        "@typescript-eslint/eslint-plugin": "^6.0.0",
        "@typescript-eslint/parser": "^6.0.0",
        "eslint": "^8.42.0",
        "eslint-config-prettier": "^8.8.0",
        "eslint-plugin-prettier": "^4.2.1",
        "jest": "^29.5.0",
        "prettier": "^2.8.8",
        "source-map-support": "^0.5.21",
        "supertest": "^6.3.3",
        "ts-jest": "^29.1.0",
        "ts-loader": "^9.4.3",
        "ts-node": "^10.9.1",
        "tsconfig-paths": "^4.2.1",
        "typescript": "^5.1.3",
    },
    "jest": {
        "moduleFileExtensions": ["js", "json", "ts"],
        "rootDir": "src",
        "testRegex": ".*\\.spec\\.ts$",
        "transform": {"^.+\\.(t|j)s$": "ts-jest"},
        "collectCoverageFrom": ["**/*.(t|j)s"],
        "coverageDirectory": "../coverage",
        "testEnvironment": "node",
    },
}


class NestJSPlugin(FrameworkPlugin):
    """Plugin for generating NestJS-specific settings code."""

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
        """Map logical template names to NestJS-specific template files."""
        return {
            "configuration": "templates/variants/nestjs/configuration.ts.j2",
            "settings_service": "templates/variants/nestjs/settings.service.ts.j2",
            "health": "templates/vendor/nestjs/settings.health.ts.j2",
            "settings_controller": "templates/variants/nestjs/settings.controller.ts.j2",
            "settings_module": "templates/variants/nestjs/settings.module.ts.j2",
            "metadata": "templates/variants/nestjs/settings.metadata.ts.j2",
            "integration_tests": "templates/tests/integration/settings.integration.spec.ts.j2",
            "e2e_tests": "templates/variants/nestjs/tests/settings.e2e-spec.ts",
        }

    def get_output_paths(self) -> Dict[str, str]:
        """Map logical names to NestJS output file paths."""
        return {
            "configuration": "src/modules/free/essentials/settings/configuration.ts",
            "settings_service": "src/modules/free/essentials/settings/settings.service.ts",
            "settings_controller": "src/modules/free/essentials/settings/settings.controller.ts",
            "settings_module": "src/modules/free/essentials/settings/settings.module.ts",
            "health": "src/health/settings.health.ts",
            "metadata": "src/modules/free/essentials/settings/settings.metadata.ts",
            "integration_tests": "tests/modules/integration/essentials/settings/settings.integration.spec.ts",
            "e2e_tests": "tests/modules/e2e/free/essentials/settings/settings.e2e-spec.ts",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        """Add NestJS-specific context variables."""
        context = dict(base_context)
        module_name = str(
            context.get("module_name") or context.get("rapidkit_vendor_module") or "settings"
        )
        module_segment = module_name.split("/")[-1]

        context.setdefault("module_slug", module_segment)
        context.setdefault("module_kebab", module_segment.replace("_", "-"))
        context.setdefault("module_basename", module_segment)

        context.update(
            framework="nestjs",
            framework_display_name="NestJS",
            language="typescript",
            import_statement="import { Module } from '@nestjs/common'",
            framework_features={
                "dependency_injection": True,
                "decorators": True,
                "modules": True,
                "middleware_support": True,
                "guards_interceptors": True,
            },
            config_decorators={
                "injectable": "@Injectable()",
                "config_service": "@Inject(ConfigService)",
                "module": "@Module({})",
                "global": "@Global()",
            },
            nestjs_imports=[
                "ConfigModule",
                "ConfigService",
                "ConfigType",
            ],
            vendor_configuration_relative="nestjs/configuration.js",
        )
        return context

    def validate_requirements(self) -> List[str]:
        """Validate NestJS-specific requirements."""
        errors = []

        # Check if Node.js is available
        node_bin = shutil.which("node")
        npm_bin = shutil.which("npm")

        if not node_bin:
            errors.append("Node.js is required for NestJS development")
        else:
            # Check Node.js version
            try:
                result = subprocess.run(  # nosec
                    [node_bin, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,  # We check returncode manually
                )
                if result.returncode == 0:
                    version = result.stdout.strip().lstrip("v")
                    major_version = int(version.split(".")[0])
                    if major_version < MIN_NODE_VERSION:
                        errors.append(
                            f"Node.js version {version} is too old. NestJS requires Node.js 16+"
                        )
                else:
                    errors.append("Failed to determine Node.js version")
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                errors.append("Failed to check Node.js version")

        if not npm_bin:
            errors.append("npm is required for NestJS package management")

        # Check if TypeScript is available (optional check)
        tsc_bin = shutil.which("tsc") or shutil.which("npx")
        if not tsc_bin:
            errors.append("TypeScript compiler not found - install with: npm install -g typescript")

        return errors

    def get_dependencies(self) -> List[str]:
        """Get NestJS-specific dependencies."""
        return [
            "@nestjs/core",
            "@nestjs/common",
            "@nestjs/config",
            "@nestjs/platform-express",
            "class-validator",
            "class-transformer",
            "reflect-metadata",
            "rxjs",
        ]

    def get_dev_dependencies(self) -> List[str]:
        """Get development dependencies for NestJS."""
        return [
            "@types/node",
            "@types/express",
            "@typescript-eslint/eslint-plugin",
            "@typescript-eslint/parser",
            "eslint",
            "jest",
            "@types/jest",
            "@types/supertest",
            "supertest",
            "ts-jest",
            "typescript",
        ]

    def pre_generation_hook(self, output_dir: Path) -> None:
        """Prepare NestJS-specific setup before generation."""

        base = output_dir / "src" / "modules" / "free" / "essentials" / "settings"
        base.mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "essentials" / "settings").mkdir(
            parents=True, exist_ok=True
        )

        tsconfig_path = output_dir / "tsconfig.json"
        package_path = output_dir / "package.json"

        self._ensure_tsconfig(tsconfig_path)
        self._ensure_package_json(package_path)

        (output_dir / "src" / "health").mkdir(parents=True, exist_ok=True)

    def post_generation_hook(self, output_dir: Path) -> None:
        """Perform NestJS-specific cleanup after generation."""
        # Downstream projects can extend this to run formatters if desired.
        _ = output_dir

    def _ensure_tsconfig(self, tsconfig_path: Path) -> None:
        if tsconfig_path.exists():
            try:
                current = json.loads(tsconfig_path.read_text())
            except json.JSONDecodeError:
                logger.warning(
                    "Existing tsconfig.json is not valid JSON; skipping automatic updates"
                )
                return

            compiler_options = current.setdefault("compilerOptions", {})
            updated = False

            for key, value in _DEFAULT_TSCONFIG["compilerOptions"].items():
                if key not in compiler_options:
                    compiler_options[key] = value
                    updated = True

            if updated:
                tsconfig_path.write_text(json.dumps(current, indent=2) + "\n")
                logger.info("Updated tsconfig.json with missing compiler options")
            return

        tsconfig_path.parent.mkdir(parents=True, exist_ok=True)
        tsconfig_path.write_text(json.dumps(_DEFAULT_TSCONFIG, indent=2) + "\n")
        logger.info("Created tsconfig.json scaffold for NestJS settings module")

    def _ensure_package_json(self, package_path: Path) -> None:
        if package_path.exists():
            try:
                current = json.loads(package_path.read_text())
            except json.JSONDecodeError:
                logger.warning(
                    "Existing package.json is not valid JSON; skipping automatic updates"
                )
                return

            updated = False

            for section in ("dependencies", "devDependencies", "scripts"):
                default_section = _DEFAULT_PACKAGE_JSON.get(section, {})
                if not isinstance(default_section, dict):
                    continue

                target_section = current.setdefault(section, {})
                if not isinstance(target_section, dict):
                    logger.warning(
                        "package.json section '%s' is not a mapping; skipping merge", section
                    )
                    continue

                for key, value in default_section.items():
                    if key not in target_section:
                        target_section[key] = value
                        updated = True

            for root_key in ("name", "version", "description", "private", "license"):
                if root_key not in current:
                    current[root_key] = _DEFAULT_PACKAGE_JSON[root_key]
                    updated = True

            if updated:
                package_path.write_text(json.dumps(current, indent=2) + "\n")
                logger.info("Augmented existing package.json with NestJS defaults")
            return

        package_path.write_text(json.dumps(_DEFAULT_PACKAGE_JSON, indent=2) + "\n")
        logger.info("Created package.json scaffold for NestJS settings module")

    def get_documentation_urls(self) -> Dict[str, str]:
        """Get NestJS documentation URLs."""
        return {
            "framework_docs": "https://docs.nestjs.com/",
            "config_docs": "https://docs.nestjs.com/techniques/configuration",
            "cli_docs": "https://docs.nestjs.com/cli/overview",
            "typescript_setup": "https://docs.nestjs.com/recipes/swc",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        """Get example NestJS configurations."""
        return {
            "app": {
                "name": "My NestJS App",
                "version": "1.0.0",
                "description": "A NestJS application with settings management",
                "port": 3000,
            },
            "database": {
                "type": "postgres",
                "host": "localhost",
                "port": 5432,
                "username": "postgres",
                "password": "password",
                "database": "mydb",
                "synchronize": True,
            },
            "jwt": {
                "secret": "your-secret-key",
                "expiresIn": "24h",
            },
            "cors": {
                "origin": ["http://localhost:3000", "http://localhost:4200"],
                "credentials": True,
            },
        }


class NestJSStandardPlugin(NestJSPlugin):
    """Alias plugin used by the nestjs.standard kit profile."""

    @property
    def name(self) -> str:  # noqa: D401
        return "nestjs.standard"

    @property
    def display_name(self) -> str:
        return "NestJS (standard kit)"
