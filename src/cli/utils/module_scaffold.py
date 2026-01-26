"""Utilities to scaffold new RapidKit modules following the lean spec."""

from __future__ import annotations

import hashlib
from pathlib import Path
from string import Template
from typing import Dict, List, Mapping

from .scaffold.constants import (
    MODULES_ROOT,
    REPO_ROOT,
    REPOSITORY_INTEGRATION_SUFFIX,
    REPOSITORY_TEST_SUFFIXES,
)
from .scaffold.identifiers import derive_identifiers
from .scaffold.result import ModuleScaffoldResult
from .scaffold.templates import (
    build_module_files,
    repository_generator_test_template,
    repository_integration_test_template,
    repository_tests_conftest_template,
    repository_tests_init_template,
    repository_unit_test_template,
)


class ModuleScaffolder:
    """Create a module skeleton with sensible defaults."""

    def __init__(self, modules_root: Path | None = None) -> None:
        self.modules_root = modules_root or MODULES_ROOT

    @staticmethod
    def _write_scaffold_file(
        destination: Path,
        content: str,
        *,
        force: bool,
        dry_run: bool,
        created: List[Path],
        skipped: List[Path],
        overwritten: List[Path],
    ) -> None:
        """Write text content to disk while tracking scaffold actions."""

        if destination.exists():
            if dry_run or not force or destination.is_dir():
                skipped.append(destination)
                return
            overwritten.append(destination)
        else:
            created.append(destination)

        if dry_run:
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    def create_module(
        self,
        *,
        tier: str,
        category: str,
        module_name: str,
        description: str | None = None,
        blueprint: str | None = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> ModuleScaffoldResult:
        slug = self._build_slug(tier, category, module_name)
        module_path = self.modules_root / slug

        if module_path.exists() and not force and not dry_run:
            raise ValueError(
                f"Module directory '{module_path}' already exists. Use --force to overwrite individual files."
            )

        identifiers = self._derive_identifiers(tier, category, module_name, description, blueprint)
        files_map = self._build_files_map(identifiers)

        created: List[Path] = []
        skipped: List[Path] = []
        overwritten: List[Path] = []

        for relative_path, template in files_map.items():
            destination = module_path / relative_path
            content = template.substitute(identifiers)
            self._write_scaffold_file(
                destination,
                content,
                force=force,
                dry_run=dry_run,
                created=created,
                skipped=skipped,
                overwritten=overwritten,
            )

        self._ensure_repository_tests(
            identifiers,
            force=force,
            dry_run=dry_run,
            created=created,
            skipped=skipped,
            overwritten=overwritten,
        )

        if not dry_run:
            self._ensure_module_file_hashes(module_path)

        return ModuleScaffoldResult(
            module_path=module_path,
            created_files=created,
            skipped_files=skipped,
            overwritten_files=overwritten,
            context=dict(identifiers),
        )

    @staticmethod
    def _ensure_module_file_hashes(module_path: Path) -> None:
        module_yaml_path = module_path / "module.yaml"
        if not module_yaml_path.exists():
            return

        raw = module_yaml_path.read_text(encoding="utf-8")
        if "\nfile_hashes:\n" in f"\n{raw}":
            return

        candidates = [
            Path("README.md"),
            Path("__init__.py"),
            Path("config/base.yaml"),
            Path("config/snippets.yaml"),
            Path("docs/README.md"),
            Path("docs/overview.md"),
            Path("docs/usage.md"),
            Path("docs/advanced.md"),
            Path("docs/changelog.md"),
            Path("docs/migration.md"),
            Path("docs/troubleshooting.md"),
            Path("docs/api-reference.md"),
            Path("templates/vendor/nestjs/configuration.js.j2"),
        ]

        file_hashes: dict[str, str] = {}
        for relative in candidates:
            absolute = module_path / relative
            if not absolute.is_file():
                continue
            digest = hashlib.sha256(absolute.read_bytes()).hexdigest()
            file_hashes[relative.as_posix()] = f"sha256:{digest}"

        if not file_hashes:
            return

        lines = ["file_hashes:"]
        for key in sorted(file_hashes):
            lines.append(f"  {key}: {file_hashes[key]}")

        rendered = raw
        if not rendered.endswith("\n"):
            rendered += "\n"
        rendered += "\n" + "\n".join(lines) + "\n"
        module_yaml_path.write_text(rendered, encoding="utf-8")

    @staticmethod
    def _build_slug(tier: str, category: str, module_name: str) -> Path:
        slug_parts = [tier.strip("/"), *(part for part in category.split("/") if part), module_name]
        return Path(*slug_parts)

    @staticmethod
    def _derive_identifiers(
        tier: str,
        category: str,
        module_name: str,
        description: str | None,
        blueprint: str | None,
    ) -> Dict[str, str]:
        return derive_identifiers(tier, category, module_name, description, blueprint)

    @staticmethod
    def _build_files_map(identifiers: Mapping[str, str]) -> Mapping[Path, Template]:
        return build_module_files(identifiers)

    def _ensure_repository_tests(
        self,
        identifiers: Mapping[str, str],
        *,
        force: bool,
        dry_run: bool,
        created: List[Path],
        skipped: List[Path],
        overwritten: List[Path],
    ) -> None:
        repo_test_rel = identifiers.get("tests_repo_relative")
        if not repo_test_rel:
            return

        repo_test_dir = REPO_ROOT / repo_test_rel
        module_name = identifiers["module_name"]

        support_files = {
            repo_test_dir / "__init__.py": repository_tests_init_template(identifiers),
            repo_test_dir / "conftest.py": repository_tests_conftest_template(identifiers),
        }

        for destination, content in support_files.items():
            self._write_scaffold_file(
                destination,
                content,
                force=force,
                dry_run=dry_run,
                created=created,
                skipped=skipped,
                overwritten=overwritten,
            )

        for suffix in REPOSITORY_TEST_SUFFIXES:
            destination = repo_test_dir / f"test_{module_name}_{suffix}.py"
            if suffix == "generator":
                content = repository_generator_test_template(identifiers)
            elif suffix == REPOSITORY_INTEGRATION_SUFFIX:
                content = repository_integration_test_template(identifiers)
            else:
                content = repository_unit_test_template(identifiers, suffix)
            self._write_scaffold_file(
                destination,
                content,
                force=force,
                dry_run=dry_run,
                created=created,
                skipped=skipped,
                overwritten=overwritten,
            )

        integration_rel = identifiers.get("tests_integration_relative")
        if integration_rel:
            integration_dir = REPO_ROOT / integration_rel
            integration_init = integration_dir / "__init__.py"
            self._write_scaffold_file(
                integration_init,
                repository_tests_init_template(identifiers),
                force=force,
                dry_run=dry_run,
                created=created,
                skipped=skipped,
                overwritten=overwritten,
            )

            integration_test_path = (
                integration_dir / f"test_{module_name}_{REPOSITORY_INTEGRATION_SUFFIX}.py"
            )
            integration_content = repository_integration_test_template(identifiers)
            self._write_scaffold_file(
                integration_test_path,
                integration_content,
                force=force,
                dry_run=dry_run,
                created=created,
                skipped=skipped,
                overwritten=overwritten,
            )


__all__ = ["ModuleScaffolder"]
