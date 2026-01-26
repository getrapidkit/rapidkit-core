"""Repository-level test template helpers for module scaffolding."""

from __future__ import annotations

import textwrap
from string import Template
from typing import Mapping

PLACEHOLDER_SKIP = textwrap.dedent(
    """
    import pytest


    pytestmark = pytest.mark.skip("Replace scaffold placeholder with real tests once implementation is ready.")
    """
).strip()


def repository_generator_test_template(identifiers: Mapping[str, str]) -> str:
    module_import_path = identifiers.get("module_import_path", "")
    module_name = identifiers["module_name"]
    return textwrap.dedent(
        f"""
        from importlib import import_module


        def test_{module_name}_generator_entrypoint() -> None:
            \"\"\"Ensure the module generator can be imported without crashing.\"\"\"

            generator_module = import_module("{module_import_path}.generate")
            assert hasattr(generator_module, "main"), "Expected a main() entrypoint on the generator module"
        """
    ).strip()


def repository_integration_test_template(identifiers: Mapping[str, str]) -> str:
    module_slug_test_path = identifiers.get("module_slug_test_path", identifiers["module_name"])
    module_import_path = identifiers.get("module_import_path", "")
    module_relative = module_import_path.replace(".", "/") if module_import_path else ""
    return textwrap.dedent(
        f"""
        from pathlib import Path


        def test_{module_slug_test_path}_integration_placeholder() -> None:
            \"\"\"Validate that the generated module runtime exists within the repository.\"\"\"

            repo_root = Path(__file__).resolve().parents[3]
            module_path = repo_root / "{module_relative}"
            assert module_path.exists(), "Generated module runtime path should exist before running integration tests"
        """
    ).strip()


def repository_unit_test_template(identifiers: Mapping[str, str], suffix: str) -> str:
    module_name = identifiers["module_name"]
    module_title = identifiers.get("module_title", module_name.replace("_", " ").title())
    guidance = {
        "overrides": "Exercise the override manager to ensure custom user behaviour is preserved.",
        "runtime": "Load the generated runtime module and assert core service behaviour.",
        "adapters": "Test adapter wiring or integration points introduced by the module.",
        "validation": "Cover schema validation and error messaging for invalid configuration.",
        "error_handling": "Ensure failures surface helpful guidance without leaking secrets.",
        "health_check": "Assert health endpoints and diagnostic utilities report correct status.",
        "framework_variants": "Render both FastAPI and NestJS variants and compare expected artefacts.",
        "vendor_layer": "Render vendor snapshots and confirm they match module.yaml declarations.",
        "configuration": "Verify config/base.yaml defaults and snippet bundles compose as expected.",
        "versioning": "Guard semantic version bumps using modules.shared.versioning utilities.",
        "standard_module": "End-to-end smoke test covering generator, runtime, frameworks, and docs.",
    }
    doc_line = guidance.get(
        suffix, "Replace this scaffold with relevant assertions for the module under test."
    )
    template = Template(
        textwrap.dedent(
            """
            ${placeholder}


            def test_${module_name}_${suffix}_placeholder() -> None:
                \"\"\"${module_title}: ${doc_line}\"\"\"

                assert True
            """
        ).strip()
    )
    return template.substitute(
        placeholder=PLACEHOLDER_SKIP,
        module_name=module_name,
        suffix=suffix,
        module_title=module_title,
        doc_line=doc_line,
    )


def repository_tests_init_template(identifiers: Mapping[str, str]) -> str:
    module_title = identifiers.get("module_title", "RapidKit")
    return textwrap.dedent(f'"""Repository test package for the {module_title} module."""').strip()


def repository_tests_conftest_template(identifiers: Mapping[str, str]) -> str:
    module_title = identifiers.get("module_title", "RapidKit")
    module_name = identifiers["module_name"]
    template = Template(
        textwrap.dedent(
            """
            from pathlib import Path

            import pytest


            @pytest.fixture(name="module_test_context")
            def module_test_context_fixture(tmp_path: Path) -> dict[str, object]:
                \"\"\"Provide an isolated workspace for ${module_title} module tests.\"\"\"

                working_dir = tmp_path / "${module_name}"
                working_dir.mkdir(parents=True, exist_ok=True)
                return {
                    "module_name": "${module_name}",
                    "workspace": working_dir,
                    "context_file": working_dir / "context.json",
                }
            """
        ).strip()
    )
    return template.substitute(module_title=module_title, module_name=module_name)


__all__ = [
    "repository_generator_test_template",
    "repository_integration_test_template",
    "repository_unit_test_template",
    "repository_tests_init_template",
    "repository_tests_conftest_template",
]
