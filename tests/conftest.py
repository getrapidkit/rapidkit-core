"""
Test configuration and shared fixtures for RapidKit

This module provides:
- Shared test fixtures and utilities
- Test data setup and teardown
- Mock configurations
- Test environment management
"""

import contextlib
import importlib.util
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

import pytest

# Ensure `src/` is on sys.path early so optional imports below succeed when pytest
# imports this module. This keeps fixture seeding working in local test runs.
root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

# Force-load project core package early to avoid collisions with similarly named deps.
import core as _core  # noqa: E402
import core.module_sign as _core_module_sign  # noqa: E402

sys.modules["core"] = _core
sys.modules["core.module_sign"] = _core_module_sign
_core.module_sign = _core_module_sign

# Ensure runtime health package aliases legacy paths before tests import them.
with contextlib.suppress(ImportError):
    import importlib

    runtime_health_pkg = importlib.import_module("runtime.core.health")
    # Canonical: register runtime health under the `src.health` alias only.
    sys.modules.setdefault("src.health", runtime_health_pkg)
    sys.modules.setdefault("core.health", runtime_health_pkg)

    for optional_module in (
        "runtime.core.health.deployment",
        "runtime.core.health.middleware",
    ):
        with contextlib.suppress(ImportError):
            importlib.import_module(optional_module)

    runtime_db_pkg = importlib.import_module("runtime.core.database")
    with contextlib.suppress(ImportError):
        importlib.import_module("runtime.core.database.postgres")
    sys.modules.setdefault("core.database", runtime_db_pkg)

    core_pkg = sys.modules.get("core")
    if core_pkg is not None:
        core_pkg.health = runtime_health_pkg
        core_pkg.database = runtime_db_pkg

    # Note: we intentionally avoid creating/patching any legacy core aliases in tests.

# Optional callable/type placeholders for conditional imports
_collect_module_files: Optional[
    Callable[[str, str, Dict[str, Any]], List[Tuple[str, Dict[str, Any]]]]
] = None
MODULES_PATH: Optional[Path] = None
render_template: Optional[Callable[..., Any]] = None
load_module_config: Optional[Callable[..., Any]] = None
record_file_hash: Optional[Callable[..., Any]] = None
save_hashes: Optional[Callable[..., Any]] = None
load_hashes: Optional[Callable[..., Any]] = None

try:  # optional helper imports for seeding rendered templates in test boilerplates
    from cli.commands.diff import _collect_module_files
    from core.rendering.template_renderer import render_template
    from core.services.config_loader import (
        MODULES_PATH as _CL_MODULES_PATH,
        load_module_config,
    )
    from core.services.file_hash_registry import (
        load_hashes,
        record_file_hash,
        save_hashes,
    )

    # If config_loader exposes MODULES_PATH, use it so tests can find module templates
    if "MODULES_PATH" in globals() and _CL_MODULES_PATH is not None:
        MODULES_PATH = _CL_MODULES_PATH
except (ImportError, OSError):  # pragma: no cover - best-effort on test environment
    _collect_module_files = None
    MODULES_PATH = None
    render_template = None
    load_module_config = None
    record_file_hash = None
    save_hashes = None
    load_hashes = None


def pytest_configure() -> None:  # pragma: no cover
    """Ensure src/ is on sys.path for imports when running tests locally."""
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def discover_boilerplates() -> List[str]:
    root = Path("boilerplates")
    if not root.exists():
        return []
    return sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir() and any((p / m).exists() for m in [".rapidkit", "template.yaml", ".env"])
    )


@pytest.fixture(scope="session")
def primary_project_name() -> str:
    env_choice = os.getenv("RAPIDKIT_TEST_PROJECT")
    if env_choice:
        return env_choice
    found = discover_boilerplates()
    if not found:
        pytest.skip("No boilerplate project found")
    return found[0]


@pytest.fixture(autouse=True)
def _preserve_cwd() -> Generator[None, None, None]:
    """Ensure tests leave the working directory unchanged."""
    original_cwd = Path.cwd()
    try:
        yield
    finally:
        os.chdir(original_cwd)


@pytest.fixture
def temp_project(tmp_path: Path, primary_project_name: str) -> Generator[Path, None, None]:
    source = Path("boilerplates") / primary_project_name
    if not source.exists():
        pytest.skip(f"Boilerplate {primary_project_name} missing")

    target_root = tmp_path
    target_proj = target_root / "boilerplates" / primary_project_name
    shutil.copytree(source, target_proj, dirs_exist_ok=True)
    (target_proj / ".rapidkit").mkdir(exist_ok=True)

    # Best-effort: seed the temp project with rendered templates for 'logging'
    if (
        _collect_module_files is not None
        and MODULES_PATH is not None
        and render_template is not None
        and load_module_config is not None
    ):
        try:
            cfg = load_module_config("logging", "fastapi/standard")
            files = _collect_module_files("logging", "fastapi/standard", cfg)

            registry = load_hashes(target_proj) if load_hashes is not None else {"files": {}}

            for ctx, entry in files:
                rel = entry.get("path") if isinstance(entry, dict) else entry
                if not rel:
                    continue

                # Determine template path
                template_file = entry.get("template") if isinstance(entry, dict) else None
                if template_file:
                    template_path = MODULES_PATH / "logging" / template_file
                else:
                    template_path = (
                        MODULES_PATH
                        / "logging"
                        / "templates"
                        / ("base" if ctx == "base" else f"overrides/{ctx}")
                        / f"{rel}.j2"
                    )
                    if not template_path.exists():
                        overrides_dir = MODULES_PATH / "logging" / "templates" / "overrides"
                        if overrides_dir.exists():
                            target_suffix = f"{rel}.j2"
                            for cand in overrides_dir.glob("**/*.j2"):
                                if cand.as_posix().endswith(target_suffix):
                                    template_path = cand
                                    break

                # Destination path
                root_path = cfg.get("root_path", "") or ""
                root_path = root_path.lstrip("/")
                dst = target_proj / root_path / rel

                if template_path.exists() and not dst.exists():
                    try:
                        content = render_template(template_path, {}) or ""
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_text(content, encoding="utf-8")

                        if record_file_hash is not None:
                            with contextlib.suppress(OSError, ValueError):
                                mod_version = cfg.get("version") or "0.0.0"
                                from pathlib import Path as _P

                                rel_path = (
                                    str((_P(root_path) / rel).as_posix()).lstrip("/")
                                    if root_path
                                    else rel
                                )
                                record_file_hash(
                                    registry,
                                    rel_path,
                                    "logging",
                                    str(mod_version),
                                    content.encode("utf-8"),
                                    previous_hash=None,
                                    snapshot=False,
                                    project_root=target_proj,
                                )
                    except (OSError, ValueError):
                        pass

            # Persist registry
            if save_hashes is not None:
                with contextlib.suppress(OSError, ValueError):
                    save_hashes(target_proj, registry)

        except (ImportError, OSError, ValueError):
            # Ignore all import/operation errors during seeding
            pass

    old_cwd = Path.cwd()
    os.chdir(target_root)
    try:
        yield target_proj
    finally:
        os.chdir(old_cwd)


@pytest.fixture()
def _temp_project(temp_project: Path) -> Path:  # pragma: no cover - simple alias
    return temp_project


@pytest.fixture(scope="session")
def rapidkit_cli_args() -> Tuple[str, ...]:  # pragma: no cover - simple factory helper
    explicit = os.getenv("RAPIDKIT_CLI_EXECUTABLE")
    if explicit:
        return tuple(shlex.split(explicit))

    if importlib.util.find_spec("rapidkit_cli") is not None:
        return (sys.executable, "-m", "rapidkit_cli")

    fallback = Path(__file__).resolve().parents[1] / "rapidkit_cli.py"
    if fallback.exists():
        return (sys.executable, str(fallback))

    return (sys.executable, "-m", "rapidkit_cli")


@pytest.fixture(scope="session")
def rapidkit_simulator(tmp_path_factory, rapidkit_cli_args):  # pragma: no cover - heavy fixture
    from tests.utils.rapidkit_simulator import RapidKitModuleSimulator

    simulator = RapidKitModuleSimulator(tmp_path_factory, rapidkit_cli_args)
    if not simulator.is_available:
        pytest.skip("RapidKit CLI is unavailable for end-to-end simulations")
    return simulator


def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: Any) -> None:
    """Print extra test summary with percentages."""
    del exitstatus, config
    # Derive total from reporter stats to avoid accessing protected attributes
    total = sum(len(v) for v in terminalreporter.stats.values())
    passed = len(terminalreporter.stats.get("passed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    failed = len(terminalreporter.stats.get("failed", []))
    xfailed = len(terminalreporter.stats.get("xfailed", []))
    xpassed = len(terminalreporter.stats.get("xpassed", []))

    pct_passed = (passed / total) * 100 if total else 0.0
    terminalreporter.write_sep("-", f"Test summary: {passed}/{total} passed ({pct_passed:.1f}%)")
    terminalreporter.write_line(
        f"Skipped: {skipped}, Failed: {failed}, Xfailed: {xfailed}, Xpassed: {xpassed}"
    )
