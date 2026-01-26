#!/usr/bin/env python3
"""CI helper to validate module structure and generator stability."""

from __future__ import annotations

import argparse
import importlib.util
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

try:  # The helper script is not packaged inside every tier distribution build
    from ensure_template_dependencies import ensure as ensure_template_dependencies
except ModuleNotFoundError:  # pragma: no cover - executed only inside dist-test bundles
    REQUIRED_TEMPLATE_PACKAGES = ("jinja2",)

    def _installed(package: str) -> bool:
        return importlib.util.find_spec(package) is not None

    def ensure_template_dependencies(install_missing: bool = False) -> Sequence[str]:
        missing = tuple(pkg for pkg in REQUIRED_TEMPLATE_PACKAGES if not _installed(pkg))
        if missing and install_missing:
            subprocess.run([sys.executable, "-m", "pip", "install", *missing], check=True)
            missing = tuple(pkg for pkg in REQUIRED_TEMPLATE_PACKAGES if not _installed(pkg))
        return missing


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
MODULE_SLUG = "free/essentials/settings"
MODULE_ROOT = SRC_ROOT / "modules" / MODULE_SLUG
NESTJS_SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "check_nestjs_smoke.js"


def ensure_python_path(env: dict[str, str]) -> str:
    """Ensure PYTHONPATH contains project root and src directory."""

    src_path = str(SRC_ROOT)
    existing_path = env.get("PYTHONPATH")
    combined = f"{src_path}{os.pathsep}{existing_path}" if existing_path else src_path

    current_dir = str(PROJECT_ROOT)
    env["PYTHONPATH"] = f"{current_dir}{os.pathsep}{combined}"
    return env["PYTHONPATH"]


if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.services.module_structure_validator import ensure_module_structure  # noqa: E402


def _compile_python_module(module_path: Path) -> None:
    py_compile.compile(str(module_path), doraise=True)


def _load_generated_settings(module_path: Path, vendor_root: Path, *, project_root: Path) -> None:
    original_vendor = os.environ.get("RAPIDKIT_VENDOR_ROOT")
    sys_path_snapshot = list(sys.path)
    try:
        os.environ["RAPIDKIT_VENDOR_ROOT"] = str(vendor_root)
        # Ensure the generated project root is importable so `import src...` works.
        sys.path.insert(0, str(project_root))

        spec = importlib.util.spec_from_file_location("generated_settings", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load generated settings module at {module_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Instantiate settings to ensure defaults + vendor wiring work
        settings_obj = module.Settings()
        if not getattr(settings_obj, "CONFIG_FILES", None):
            raise RuntimeError("Generated Settings instance missing CONFIG_FILES payload")
    finally:
        sys.path[:] = sys_path_snapshot
        if original_vendor is None:
            os.environ.pop("RAPIDKIT_VENDOR_ROOT", None)
        else:
            os.environ["RAPIDKIT_VENDOR_ROOT"] = original_vendor


def validate_fastapi_runtime(target_dir: Path) -> None:
    fastapi_settings = (
        target_dir / "src" / "modules" / "free" / "essentials" / "settings" / "settings.py"
    )
    vendor_root = target_dir / ".rapidkit" / "vendor"
    if not fastapi_settings.exists():
        raise RuntimeError(f"FastAPI settings artifact missing at {fastapi_settings}")
    if not vendor_root.exists():
        raise RuntimeError("Vendor snapshot missing after generator run")

    _compile_python_module(fastapi_settings)
    _load_generated_settings(fastapi_settings, vendor_root, project_root=target_dir)


def _is_installed(package: str) -> bool:
    return importlib.util.find_spec(package) is not None


def run_generator_smoke(
    validate_runtime: bool = True, keep_artifacts: bool = False, include_nestjs: bool = True
) -> None:
    target_dir = Path(tempfile.mkdtemp(prefix="settings-generator-smoke-"))
    try:
        variants: list[str] = []

        if _is_installed("fastapi"):
            variants.append("fastapi")
        else:
            print(
                "WARN Skipping FastAPI generator smoke: fastapi is not installed", file=sys.stderr
            )
            validate_runtime = False

        if include_nestjs:
            variants.append("nestjs")

        if not variants:
            print("WARN No generator variants to validate", file=sys.stderr)
            return

        # Ensure src directory is in Python path
        env = os.environ.copy()
        python_path = ensure_python_path(env)

        print(f"Using PYTHONPATH: {python_path}")
        print(f"SRC_ROOT exists: {SRC_ROOT.exists()}")
        print(f"MODULE_ROOT exists: {MODULE_ROOT.exists()}")

        for variant in variants:
            print(f"Testing {variant} variant...")

            # First try: subprocess with PYTHONPATH
            subprocess_error = None
            try:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "modules.free.essentials.settings.generate",
                        variant,
                        str(target_dir),
                    ],
                    check=True,
                    env=env,
                    cwd=PROJECT_ROOT,  # Ensure we run from project root
                )
                print(f"OK {variant} variant succeeded via subprocess")
                continue  # Skip to next variant if successful
            except subprocess.CalledProcessError as e:
                subprocess_error = e
                print(f"WARN Subprocess failed for {variant}, trying direct import...")

            # Second try: direct import and execution
            try:
                # Add src to sys.path if not already there
                if str(SRC_ROOT) not in sys.path:
                    sys.path.insert(0, str(SRC_ROOT))
                if str(PROJECT_ROOT) not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT))

                # Import and run the module directly
                import modules.free.essentials.settings.generate as gen_module

                # Temporarily modify sys.argv for the main function
                original_argv = sys.argv[:]
                sys.argv = ["generate.py", variant, str(target_dir)]
                try:
                    gen_module.main()
                    print(f"OK {variant} variant succeeded via direct import")
                finally:
                    sys.argv = original_argv

            except (ImportError, RuntimeError, OSError) as direct_e:
                print(f"ERROR Both subprocess and direct import failed for {variant}")
                print(f"Subprocess error: {subprocess_error}")
                print(f"Direct import error: {direct_e}")
                raise RuntimeError(f"Failed to execute generator for {variant}") from direct_e

        if validate_runtime:
            validate_fastapi_runtime(target_dir)
    finally:
        if not keep_artifacts:
            shutil.rmtree(target_dir, ignore_errors=True)


def run_nestjs_smoke(strict: bool = False) -> None:
    node_bin = shutil.which("node")
    npm_bin = shutil.which("npm")
    if node_bin is None or npm_bin is None:
        message = "Skipping NestJS smoke test: Node.js or npm not available"
        if strict:
            raise RuntimeError(message)
        print(f"WARN {message}", file=sys.stderr)
        return

    if not NESTJS_SMOKE_SCRIPT.exists():
        message = f"Skipping NestJS smoke test: script {NESTJS_SMOKE_SCRIPT} not found"
        if strict:
            raise RuntimeError(message)
        print(f"WARN {message}", file=sys.stderr)
        return

    workdir = Path(tempfile.mkdtemp(prefix="settings-nestjs-smoke-"))
    try:
        env = os.environ.copy()
        python_path = ensure_python_path(env)
        env.setdefault("PYTHON", sys.executable)
        print(f"Using PYTHONPATH for NestJS smoke: {python_path}")
        subprocess.run(
            [
                node_bin,
                str(NESTJS_SMOKE_SCRIPT),
                str(PROJECT_ROOT),
                str(workdir),
            ],
            check=True,
            env=env,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate settings module integrity")
    parser.add_argument("--skip-nestjs", action="store_true", help="Skip NestJS smoke validation")
    parser.add_argument(
        "--strict-nestjs",
        action="store_true",
        help="Fail if NestJS prerequisites are missing instead of skipping",
    )
    parser.add_argument(
        "--skip-runtime-validation",
        action="store_true",
        help="Skip importing the generated FastAPI settings module",
    )
    parser.add_argument(
        "--keep-artifacts",
        action="store_true",
        help="Keep generated artifacts on disk for debugging",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    missing_template_deps = ensure_template_dependencies(install_missing=True)
    if missing_template_deps:
        raise RuntimeError(
            "Missing template dependencies: "
            + ", ".join(missing_template_deps)
            + ". Run 'poetry install --with dev' to install optional generators."
        )

    ensure_module_structure(MODULE_SLUG)
    run_generator_smoke(
        validate_runtime=not args.skip_runtime_validation,
        keep_artifacts=args.keep_artifacts,
        include_nestjs=not args.skip_nestjs,
    )
    if not args.skip_nestjs:
        run_nestjs_smoke(strict=args.strict_nestjs)


if __name__ == "__main__":
    main()
