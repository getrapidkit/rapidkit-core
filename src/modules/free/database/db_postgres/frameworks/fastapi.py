# pyright: reportMissingImports=false
"""FastAPI framework plugin for the DatabasePostgres module."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Mapping

from modules.shared.frameworks import FrameworkPlugin
from modules.shared.utils.health import (
    HealthShimSpec,
    ensure_health_package,
    ensure_vendor_health_shim,
)
from modules.shared.utils.health_specs import infer_vendor_relative, load_module_config

MODULE_ROOT = Path(__file__).resolve().parents[1]
_CONFIG = load_module_config(MODULE_ROOT)
HEALTH_SHIM_SPEC = HealthShimSpec(
    module_name="postgres",
    vendor_module=str(_CONFIG.get("name") or MODULE_ROOT.name or "module"),
    vendor_version=str(_CONFIG.get("version", "0.0.0") or "0.0.0"),
    vendor_relative_path=infer_vendor_relative(
        _CONFIG,
        "postgres_health.py.j2",
    ),
    target_relative_path="src/health/postgres.py",
    slug="postgres",
)


class FastAPIPlugin(FrameworkPlugin):
    """Plugin for generating FastAPI-oriented PostgreSQL database integrations."""

    @property
    def name(self) -> str:
        return "fastapi"

    @property
    def language(self) -> str:
        return "python"

    @property
    def display_name(self) -> str:
        return "FastAPI"

    def get_template_mappings(self) -> Dict[str, str]:
        return {
            "database": "templates/variants/fastapi/postgres.py.j2",
            "config": "templates/variants/fastapi/postgres_config.yaml.j2",
            "integration_tests": "templates/tests/integration/test_postgres_integration.j2",
        }

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "database": "src/modules/free/database/db_postgres/postgres.py",
            "config": "config/database/postgres.yaml",
            "integration_tests": "tests/modules/integration/database/test_postgres_integration.py",
        }

    def get_context_enrichments(self, base_context: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            **base_context,
            "framework": "fastapi",
            "framework_display_name": "FastAPI",
            "language": "python",
            "module_class_name": "DatabasePostgres",
            "base_module": base_context.get("base_module"),
            "database_type": "postgresql",
            "async_support": True,
            "connection_pooling": True,
            "health_checks": True,
        }

    def validate_requirements(self) -> List[str]:
        # Generation does not require external tooling; runtime dependencies are documented.
        return []

    def pre_generation_hook(self, output_dir: Path) -> None:
        module_root = output_dir / "src" / "modules" / "free" / "database" / "db_postgres"
        module_root.mkdir(parents=True, exist_ok=True)
        (output_dir / "tests" / "modules" / "integration" / "database").mkdir(
            parents=True, exist_ok=True
        )
        (output_dir / "config" / "database").mkdir(parents=True, exist_ok=True)
        ensure_health_package(
            output_dir,
            include_database=False,
            extra_imports=[("src.health.postgres", "register_postgres_health")],
        )

        with suppress(RuntimeError, OSError):
            ensure_vendor_health_shim(output_dir, spec=HEALTH_SHIM_SPEC)

    def post_generation_hook(self, output_dir: Path) -> None:
        return None

    def get_documentation_urls(self) -> Dict[str, str]:
        return {
            "framework_docs": "https://fastapi.tiangolo.com/",
            "sqlalchemy_docs": "https://docs.sqlalchemy.org/",
            "asyncpg_docs": "https://magicstack.github.io/asyncpg/",
        }

    def get_example_configurations(self) -> Dict[str, Any]:
        return {
            "database_url": "postgresql://user:password@localhost:5432/dbname",
            "pool_size": 10,
            "max_overflow": 20,
        }

    def get_dependencies(self) -> List[str]:
        return [
            "fastapi>=0.119.0",
            "sqlalchemy>=2.0.0",
            "asyncpg>=0.29.0",
            "psycopg[binary]>=3.1.0",
        ]

    def get_dev_dependencies(self) -> List[str]:
        return [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.25.0",
        ]
