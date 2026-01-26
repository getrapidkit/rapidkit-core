"""Blueprint definitions for module scaffolding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence


@dataclass(frozen=True)
class ModuleCapability:
    """Describe a capability surfaced by a scaffolded module."""

    name: str
    description: str


@dataclass(frozen=True)
class ModuleBlueprint:
    """Describes the metadata hints applied during scaffolding."""

    key: str
    display_name: str | None = None
    summary: str | None = None
    tags: Sequence[str] = field(default_factory=list)
    capabilities: Sequence[ModuleCapability] = field(default_factory=list)
    compatibility: Mapping[str, object] = field(default_factory=dict)
    testing: Mapping[str, object] = field(default_factory=dict)
    highlights: Sequence[str] = field(default_factory=list)
    base_config: Mapping[str, object] = field(default_factory=dict)
    snippet_config: Mapping[str, object] = field(default_factory=dict)

    def capability_names(self) -> List[str]:
        return [cap.name for cap in self.capabilities]

    def capability_descriptions(self) -> List[str]:
        return [cap.description for cap in self.capabilities]


_BASELINE_COMPATIBILITY: Dict[str, object] = {
    "python": ">=3.9,<4.0",
    "frameworks": ["fastapi", "nestjs"],
    "os": ["linux", "darwin", "windows"],
}

_BASELINE_TESTING: Dict[str, object] = {
    "coverage_min": 70,
    "integration_tests": True,
    "e2e_tests": False,
}


_BASELINE_BASE_CONFIG: Dict[str, object] = {
    "profiles": {
        "fastapi/standard": {
            "description": "FastAPI runtime profile for ${module_title} REST, health, and overrides integration.",
        },
        "nestjs/standard": {
            "description": "NestJS module wiring providers and controllers for ${module_title}.",
        },
        "vendor/baseline": {
            "description": "Vendor layer templates emitted for ${module_title} runtime contracts.",
        },
    },
    "variables": {
        "log_level": {
            "type": "string",
            "default": "INFO",
            "description": "Logging threshold used by ${module_title} components.",
            "validation": "^(CRITICAL|ERROR|WARNING|INFO|DEBUG|TRACE)$",
        },
        "request_timeout_seconds": {
            "type": "integer",
            "default": 30,
            "description": "Default timeout (seconds) for outbound calls initiated by ${module_title}.",
            "validation": "^[0-9]+$",
        },
        "feature_flag_enabled": {
            "type": "boolean",
            "default": False,
            "description": "Toggle demonstrating feature gating inside ${module_title} workflows.",
        },
    },
    "depends_on": {
        "fastapi/standard": [],
        "nestjs/standard": [],
    },
    "dev_dependencies": [
        {
            "name": "pytest",
            "source": "external",
            "tool": "pip",
            "version": ">=8.0.0,<9.0",
        },
        {
            "name": "pytest-asyncio",
            "source": "external",
            "tool": "pip",
            "version": ">=0.23.0,<1.0",
        },
        {
            "name": "ruff",
            "source": "external",
            "tool": "pip",
            "version": ">=0.4.0,<1.0",
        },
    ],
}


_BASELINE_SNIPPET_CONFIG: Dict[str, object] = {
    "snippets": [
        {
            "name": "${module_name}_usage_example",
            "template": "templates/snippets/${module_name}.snippet.j2",
            "description": "Injects an opinionated usage example for ${module_title}.",
        }
    ],
}


_SETTINGS_BASE_CONFIG: Dict[str, object] = {
    "profiles": {
        "fastapi/standard": {
            "description": "FastAPI settings backbone with environment, Vault, and Secrets Manager support.",
        },
        "fastapi/ddd": {
            "inherits": "fastapi/standard",
            "description": "FastAPI DDD profile inheriting standard defaults for ${module_title}.",
        },
        "nestjs/standard": {
            "description": "NestJS configuration module exposing environment-aware settings for ${module_title}.",
        },
    },
    "variables": {
        "base_module": {
            "type": "string",
            "default": "src",
            "description": "Base module path for the project.",
            "validation": "^[a-zA-Z0-9_./:-]+$",
        },
        "config_sources": {
            "type": "list",
            "default": [".env", ".env.local", "config.yaml"],
            "description": "List of configuration sources consulted by ${module_title}.",
            "item_validation": "^[a-zA-Z0-9_./-]+$",
        },
        "vault_url": {
            "type": "string",
            "default": "http://localhost:8200",
            "description": "HashiCorp Vault endpoint for secure secret retrieval.",
            "validation": "^https?://[a-zA-Z0-9_./:-]+$",
        },
        "aws_region": {
            "type": "string",
            "default": "us-east-1",
            "description": "AWS region used when integrating with Secrets Manager.",
            "validation": "^[a-z0-9-]+$",
        },
    },
    "depends_on": {
        "fastapi/standard": [
            {
                "name": "pyyaml",
                "source": "external",
                "tool": "pip",
                "version": ">=6.0.2,<7.0",
            },
            {
                "name": "hvac",
                "source": "external",
                "tool": "pip",
                "version": ">=2.3.0,<3.0",
            },
            {
                "name": "boto3",
                "source": "external",
                "tool": "pip",
                "version": ">=1.35.0,<2.0",
            },
        ],
        "nestjs/standard": [
            {
                "name": "@nestjs/config",
                "source": "external",
                "tool": "npm",
                "version": "^3.2.0",
            },
            {
                "name": "joi",
                "source": "external",
                "tool": "npm",
                "version": "^17.11.0",
            },
            {
                "name": "dotenv",
                "source": "external",
                "tool": "npm",
                "version": "^16.4.5",
            },
            {
                "name": "yaml",
                "source": "external",
                "tool": "npm",
                "version": "^2.4.2",
            },
        ],
    },
    "dev_dependencies": [
        {
            "name": "black",
            "source": "external",
            "tool": "pip",
            "version": ">=25.0.0,<26.0",
        },
        {
            "name": "isort",
            "source": "external",
            "tool": "pip",
            "version": ">=5.13.2,<6.0",
        },
        {
            "name": "mypy",
            "source": "external",
            "tool": "pip",
            "version": ">=1.10.0,<2.0",
        },
        {
            "name": "ruff",
            "source": "external",
            "tool": "pip",
            "version": ">=0.4.4,<1.0",
        },
        {
            "name": "flake8",
            "source": "external",
            "tool": "pip",
            "version": ">=7.1.0,<8.0",
        },
        {
            "name": "pytest",
            "source": "external",
            "tool": "pip",
            "version": ">=8.3.0,<9.0",
        },
        {
            "name": "pytest-asyncio",
            "source": "external",
            "tool": "pip",
            "version": ">=0.25.0,<1.0",
        },
    ],
}


_AUTH_CORE_BASE_CONFIG: Dict[str, object] = {
    "profiles": {
        "fastapi/standard": {
            "description": "FastAPI routers, services, and dependencies powering ${module_title}.",
        },
        "fastapi/internal": {
            "inherits": "fastapi/standard",
            "description": "Internal-only FastAPI profile exposing administrative operations for ${module_title}.",
        },
        "nestjs/standard": {
            "description": "NestJS services and controllers implementing ${module_title} domain flows.",
        },
    },
    "variables": {
        "access_token_ttl_minutes": {
            "type": "integer",
            "default": 30,
            "description": "Lifetime (minutes) for issued access tokens.",
            "validation": "^[0-9]+$",
        },
        "refresh_token_ttl_days": {
            "type": "integer",
            "default": 30,
            "description": "Lifetime (days) for refresh tokens.",
            "validation": "^[0-9]+$",
        },
        "password_hash_algorithm": {
            "type": "string",
            "default": "bcrypt",
            "description": "Hashing algorithm applied to user credentials.",
            "validation": "^(bcrypt|argon2)$",
        },
    },
    "depends_on": {
        "fastapi/standard": [
            {
                "name": "passlib[bcrypt]",
                "source": "external",
                "tool": "pip",
                "version": ">=1.7.4,<2.0",
            },
            {
                "name": "pyjwt[crypto]",
                "source": "external",
                "tool": "pip",
                "version": ">=2.8.0,<3.0",
            },
        ],
        "nestjs/standard": [
            {
                "name": "@nestjs/jwt",
                "source": "external",
                "tool": "npm",
                "version": "^10.2.0",
            },
            {
                "name": "bcrypt",
                "source": "external",
                "tool": "npm",
                "version": "^5.1.0",
            },
        ],
    },
    "dev_dependencies": [
        {
            "name": "pytest",
            "source": "external",
            "tool": "pip",
            "version": ">=8.3.0,<9.0",
        },
        {
            "name": "pytest-asyncio",
            "source": "external",
            "tool": "pip",
            "version": ">=0.25.0,<1.0",
        },
        {
            "name": "ruff",
            "source": "external",
            "tool": "pip",
            "version": ">=0.4.4,<1.0",
        },
    ],
}


_AUTH_CORE_SNIPPET_CONFIG: Dict[str, object] = {
    "snippets": [
        {
            "name": "${module_name}_token_validation",
            "template": "templates/snippets/${module_name}.snippet.j2",
            "description": "Example showing how to validate tokens produced by ${module_title}.",
        }
    ],
}


BLUEPRINTS: Dict[str, ModuleBlueprint] = {
    "baseline": ModuleBlueprint(
        key="baseline",
        summary=(
            "Bootstrap implementation covering vendor runtime generation, framework adapters, and health checks."
        ),
        tags=("core",),
        capabilities=(
            ModuleCapability(
                "runtime_scaffolding",
                "Generates vendor runtime files alongside framework-specific implementations.",
            ),
            ModuleCapability(
                "health_checks",
                "Includes baseline health endpoints and validation hooks for common infrastructure.",
            ),
            ModuleCapability(
                "override_support",
                "Ships override contracts enabling projects to customise behaviour without forking templates.",
            ),
        ),
        compatibility=_BASELINE_COMPATIBILITY,
        testing=_BASELINE_TESTING,
        highlights=(
            "Balanced defaults covering FastAPI and NestJS variants.",
            "Ready-to-run generator with structured module metadata.",
        ),
        base_config=_BASELINE_BASE_CONFIG,
        snippet_config=_BASELINE_SNIPPET_CONFIG,
    ),
    "settings": ModuleBlueprint(
        key="settings",
        display_name="Configuration Settings",
        summary=(
            "Centralised configuration service with hot-reload support, layered sources, and framework parity."
        ),
        tags=("config", "settings", "env"),
        capabilities=(
            ModuleCapability(
                "layered_configuration",
                "Loads configuration from environment variables, secrets stores, and project defaults.",
            ),
            ModuleCapability(
                "hot_reload",
                "Optionally reloads configuration when backing stores change to keep services in sync.",
            ),
            ModuleCapability(
                "framework_adapters",
                "Provides FastAPI dependency and NestJS provider wrappers for runtime consumption.",
            ),
        ),
        compatibility={
            "python": ">=3.10,<4.0",
            "node": ">=18",
            "frameworks": ["fastapi", "nestjs"],
            "os": ["linux", "darwin", "windows"],
            "migration_guide": "https://docs.rapidkit.top/modules/settings/migration",
        },
        testing={
            "coverage_min": 80,
            "integration_tests": True,
            "e2e_tests": False,
            "fixtures": ["conftest.py"],
        },
        highlights=(
            "Ships with layered configuration sources and runtime helpers.",
            "Includes guidance for migration and compatibility guarantees.",
        ),
        base_config=_SETTINGS_BASE_CONFIG,
        snippet_config=_BASELINE_SNIPPET_CONFIG,
    ),
    "auth_core": ModuleBlueprint(
        key="auth_core",
        display_name="Authentication Core",
        summary=(
            "Foundational authentication primitives covering password hashing, token issuance, and RBAC scaffolding."
        ),
        tags=("auth", "security", "passwords", "tokens"),
        capabilities=(
            ModuleCapability(
                "credential_workflows",
                "Provides templates for password hashing, token lifecycles, and credential validation.",
            ),
            ModuleCapability(
                "rbac_support",
                "Ships RBAC helpers to model roles and permissions across services.",
            ),
            ModuleCapability(
                "multi_framework",
                "Delivers FastAPI routes and NestJS services with consistent behaviours.",
            ),
        ),
        compatibility={
            "python": ">=3.10,<4.0",
            "node": ">=18",
            "frameworks": ["fastapi", "nestjs"],
            "os": ["linux", "darwin", "windows"],
        },
        testing={
            "coverage_min": 85,
            "integration_tests": True,
            "e2e_tests": False,
        },
        highlights=(
            "Includes ready-to-use hashing and token utilities.",
            "Scaffolds RBAC and override hooks for advanced deployments.",
        ),
        base_config=_AUTH_CORE_BASE_CONFIG,
        snippet_config=_AUTH_CORE_SNIPPET_CONFIG,
    ),
}


def get_blueprint(key: str | None) -> ModuleBlueprint:
    lookup = (key or "baseline").lower().strip()
    if lookup not in BLUEPRINTS:
        available = ", ".join(sorted(BLUEPRINTS))
        raise ValueError(f"Unknown module blueprint '{key}'. Available blueprints: {available}")
    return BLUEPRINTS[lookup]


def list_blueprint_keys() -> List[str]:
    return sorted(BLUEPRINTS)
