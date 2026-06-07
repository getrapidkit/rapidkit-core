#!/usr/bin/env python3
"""Unified RapidKit module validation helper.

This script wraps the core ``rapidkit modules`` validation commands so contributors and
CI can run a single entry point whenever module code changes. It intentionally keeps the
surface area narrow (validate structure + holistic ``vet``) but is easy to extend if a
module needs bespoke checks in the future.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULES_ROOT = REPO_ROOT / "src" / "modules"
MODULE_PATH_PREFIX = Path("src") / "modules"
MODULE_PATH_MIN_PARTS = 3
DEFAULT_MODULES = ("free/essentials/settings",)
SMOKE_REGISTRY: dict[str, Sequence[str]] = {
    "free/essentials/settings": (
        sys.executable,
        "scripts/check_module_integrity.py",
        "--strict-nestjs",
    ),
}


class ValidationError(RuntimeError):
    """Raised when one or more module validations fail."""


def _discover_modules() -> list[str]:
    modules: list[str] = []
    if not MODULES_ROOT.exists():
        return modules
    for tier_dir in MODULES_ROOT.iterdir():
        if not tier_dir.is_dir():
            continue
        for scope_dir in tier_dir.iterdir():
            if not scope_dir.is_dir():
                continue
            for module_dir in scope_dir.iterdir():
                if not module_dir.is_dir():
                    continue
                relative = module_dir.relative_to(MODULES_ROOT)
                modules.append(relative.as_posix())
    return sorted(modules)


def _normalize_modules(modules: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for module in modules:
        candidate = module.strip().strip("/")
        if not candidate:
            continue
        candidate = candidate.replace("\\", "/")
        if candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    if not normalized:
        raise ValidationError("No module identifiers received after normalization")
    return normalized


def _run(command: Sequence[str], *, cwd: Path | None = None) -> None:
    pretty = " ".join(shlex.quote(part) for part in command)
    pretty_cwd = f" (cwd={cwd})" if cwd else ""
    print("$", pretty, pretty_cwd)
    subprocess.run(command, check=True, cwd=cwd)


def _module_slug_from_path(path: Path) -> str | None:
    try:
        relative = path.relative_to(MODULE_PATH_PREFIX)
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) < MODULE_PATH_MIN_PARTS:
        return None
    candidate_dir = MODULES_ROOT.joinpath(*parts[:MODULE_PATH_MIN_PARTS])
    if not candidate_dir.is_dir():
        return None
    return "/".join(parts[:MODULE_PATH_MIN_PARTS])


def _modules_from_git_range(from_ref: str, to_ref: str) -> list[str]:
    diff_cmd = ["git", "diff", "--name-only", f"{from_ref}..{to_ref}"]
    result = subprocess.run(diff_cmd, capture_output=True, text=True, check=True)
    modules: set[str] = set()
    for raw_entry in result.stdout.splitlines():
        entry = raw_entry.strip()
        if not entry:
            continue
        slug = _module_slug_from_path(Path(entry))
        if slug:
            modules.add(slug)
    return sorted(modules)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate RapidKit modules via CLI wrappers")
    parser.add_argument(
        "--modules",
        "-m",
        action="append",
        metavar="SLUG",
        help="Module identifier relative to src/modules (e.g. free/essentials/settings). Repeatable.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate every module discovered under src/modules instead of the defaults.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Stop after the first failing command instead of aggregating errors.",
    )
    parser.add_argument(
        "--from-ref",
        metavar="REF",
        help="Git ref/commit to diff from (requires --to-ref).",
    )
    parser.add_argument(
        "--to-ref",
        metavar="REF",
        help="Git ref/commit to diff to (requires --from-ref).",
    )
    parser.add_argument(
        "--pre-commit-range",
        action="store_true",
        help="Infer git range from PRE_COMMIT_FROM_REF/TO_REF env vars.",
    )
    parser.add_argument(
        "--with-smoke",
        action="store_true",
        help="Run registered smoke suites (e.g. generator checks) after CLI validation.",
    )
    parser.add_argument(
        "--include-paid",
        action="store_true",
        help=(
            "Include paid-tier modules when validating (opt-in). "
            "By default paid modules are skipped to avoid blocking pre-push checks."
        ),
    )
    parser.add_argument(
        "--no-module-yaml-standard",
        action="store_true",
        help="Skip strict module.yaml generation.variants standard validation.",
    )

    args = parser.parse_args(argv)

    modules: list[str]
    if args.pre_commit_range:
        from_ref = os.getenv("PRE_COMMIT_FROM_REF")
        to_ref = os.getenv("PRE_COMMIT_TO_REF")
        if not from_ref or not to_ref:
            from_ref = os.getenv("RAPIDKIT_VALIDATION_BASE", "origin/main")
            to_ref = "HEAD"
        modules = _modules_from_git_range(from_ref, to_ref)
        if not modules:
            modules = list(DEFAULT_MODULES)
    elif args.from_ref or args.to_ref:
        if not (args.from_ref and args.to_ref):
            raise ValidationError("Both --from-ref and --to-ref must be provided")
        modules = _modules_from_git_range(args.from_ref, args.to_ref)
        if not modules:
            modules = list(DEFAULT_MODULES)
    elif args.all:
        modules = _discover_modules()
        if not modules:
            raise ValidationError("No modules discovered under src/modules")
    elif args.modules:
        modules = args.modules
    else:
        modules = list(DEFAULT_MODULES)

    try:
        normalized_modules = _normalize_modules(modules)
    except ValidationError as exc:
        print(f"❌ {exc}")
        return 2

    # By default exclude paid-tier modules from validation runs so pre-push
    # and other automated checks do not fail because of draft/paid work. If
    # the caller requests paid modules explicitly set --include-paid to opt-in.
    if not args.include_paid:
        filtered = [m for m in normalized_modules if m.split("/")[0].lower() != "paid"]
        if not filtered:
            print("ℹ️  No non-paid modules found to validate after filtering; nothing to do")
            return 0
        normalized_modules = filtered

    commands: list[list[str]] = []
    for module in normalized_modules:
        if not args.no_module_yaml_standard:
            commands.append(
                [
                    "poetry",
                    "run",
                    "python",
                    "scripts/validate_module_structure.py",
                    "--ensure",
                    module,
                    "--strict-module-yaml",
                    "--strict-module-yaml-schema",
                    "--only-module-yaml",
                ]
            )
        commands.append(["rapidkit", "modules", "validate-structure", module])
        commands.append(["rapidkit", "modules", "vet", module])

    errors: list[tuple[Sequence[str], subprocess.CalledProcessError]] = []
    for command in commands:
        try:
            _run(command)
        except subprocess.CalledProcessError as exc:
            errors.append((command, exc))
            if args.strict:
                break

    if not errors and args.with_smoke:
        smoke_errors: list[tuple[str, Sequence[str], subprocess.CalledProcessError]] = []
        for module in normalized_modules:
            smoke_command = SMOKE_REGISTRY.get(module)
            if not smoke_command:
                continue
            try:
                _run(smoke_command, cwd=REPO_ROOT)
            except subprocess.CalledProcessError as exc:
                smoke_errors.append((module, smoke_command, exc))
                if args.strict:
                    break
        if smoke_errors:
            print("❌ Module smoke validation failed:")
            for module, command_seq, error in smoke_errors:
                print(
                    "  -",
                    module,
                    "→",
                    " ".join(command_seq),
                    f"(exit code {error.returncode})",
                )
            return smoke_errors[0][2].returncode or 1

    if errors:
        print("❌ Module validation failed:")
        for command_seq, error in errors:
            print("  -", " ".join(command_seq), f"(exit code {error.returncode})")
        return errors[0][1].returncode or 1

    if args.with_smoke:
        print("✅ RapidKit module validation + smoke tests completed successfully")
    else:
        print("✅ RapidKit module validation completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
