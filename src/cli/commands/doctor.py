# cli/commands/doctor.py

import json
import os
import re
import shutil
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Iterable

import typer

from ..ui.printer import print_error, print_info, print_success, print_warning

doctor_app = typer.Typer(help="🩺 Diagnose your development environment")

# Minimum supported Node major version for some kits (eg. NestJS)
NODE_MIN_MAJOR = 20


@doctor_app.command("check")
def check_env(
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
    workspace: bool = typer.Option(False, "--workspace", help="Scan workspace projects"),
) -> None:
    def _find_kits_dir() -> Path | None:
        bundled = Path(__file__).parent.parent.parent / "kits"
        if bundled.exists():
            return bundled
        for candidate in [Path.cwd(), *Path.cwd().parents]:
            kits = candidate / "kits"
            if kits.exists():
                return kits
        return None

    def _iter_projects(root: Path, max_depth: int = 3) -> Iterable[Path]:
        ignore_dirs = {
            ".git",
            ".venv",
            "node_modules",
            "dist",
            "build",
            "__pycache__",
            ".rapidkit",
            ".tox",
        }
        root = root.resolve()
        for current, dirs, _files in os.walk(root):
            rel = Path(current).relative_to(root)
            if rel.parts and len(rel.parts) > max_depth:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            if ".rapidkit" in dirs:
                project_json = Path(current) / ".rapidkit" / "project.json"
                if project_json.exists():
                    yield Path(current)
                    dirs[:] = []

    def _detect_engine(project_root: Path) -> str:
        ctx_path = project_root / ".rapidkit" / "context.json"
        if ctx_path.exists():
            try:
                data = json.loads(ctx_path.read_text(encoding="utf-8"))
                if data.get("engine") == "npm":
                    return "node"
            except (OSError, json.JSONDecodeError):
                pass
        if (project_root / "package.json").exists():
            return "node"
        return "python"

    def _workspace_payload(root: Path) -> dict[str, object]:
        projects = []
        for project_root in _iter_projects(root):
            projects.append(
                {
                    "name": project_root.name,
                    "path": str(project_root),
                    "engine": _detect_engine(project_root),
                }
            )
        return {
            "root": str(root),
            "count": len(projects),
            "projects": projects,
        }

    if json_output:
        payload: dict[str, object] = {
            "schema_version": 1,
            "python": {
                "ok": sys.version_info >= (3, 8),
                "version": sys.version.split()[0],
            },
            "poetry": {
                "present": bool(shutil.which("poetry")),
            },
        }

        kits_path = _find_kits_dir()
        payload["kits"] = {
            "path": str(kits_path) if kits_path else None,
            "present": bool(kits_path and kits_path.exists()),
        }

        # project venv hints (best-effort, cwd-based)
        payload["project"] = {
            "venvPresent": Path(".venv").exists(),
        }

        node = shutil.which("node")
        node_version: str | None = None
        node_major: int | None = None
        node_ok: bool | None = None
        if node:
            try:
                out = subprocess.check_output([node, "--version"], text=True).strip()  # nosec
                node_version = out
                m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", out)
                if m:
                    node_major = int(m.group(1))
                    node_ok = node_major >= NODE_MIN_MAJOR
            except subprocess.CalledProcessError:
                node_version = None
        payload["node"] = {
            "present": bool(node),
            "path": node,
            "version": node_version,
            "major": node_major,
            "minMajor": NODE_MIN_MAJOR,
            "ok": node_ok,
        }

        pms = {
            "npm": shutil.which("npm"),
            "yarn": shutil.which("yarn"),
            "pnpm": shutil.which("pnpm"),
        }
        payload["packageManagers"] = {k: bool(v) for k, v in pms.items()}

        if workspace:
            payload["workspace"] = _workspace_payload(Path.cwd())

        typer.echo(json.dumps(payload, ensure_ascii=False))
        return

    print_info("🔬 Starting environment diagnostics...\n")

    # Check Python version
    if sys.version_info >= (3, 8):
        print_success(f"✅ Python version {sys.version.split()[0]} is OK")
    else:
        print_error("❌ Python 3.8+ required")

    # Check Poetry
    if shutil.which("poetry"):
        print_success("✅ Poetry is installed")
    else:
        print_error("❌ Poetry is not installed")

    # Check RapidKit structure
    kits_path = _find_kits_dir()
    if kits_path and kits_path.exists():
        print_success(f"✅ Kits directory found: {kits_path}")
        found_valid = False
        for kit in kits_path.iterdir():
            if kit.is_dir() and (kit / "kit.yaml").exists() and (kit / "generator.py").exists():
                found_valid = True
                break
        if found_valid:
            print_success("✅ At least one valid kit found")
        else:
            print_warning("⚠️ Kits directory present but no valid kits found")
            print_info("Tip: reinstall RapidKit core or run in the repository containing kits")
    else:
        print_info("ℹ️ Kits directory not bundled in this installation")

    # Check .venv
    if Path(".venv").exists():
        print_success("✅ .venv exists")
    else:
        print_warning("⚠️ .venv not found - consider running `poetry install`")

    print_info("\n🔍 Environment check completed.")

    # --- Node / JS ecosystem checks ---------------------------------
    print_info("\n🔬 Node / JavaScript ecosystem checks...")

    node = shutil.which("node")
    if node:
        try:
            out = subprocess.check_output([node, "--version"], text=True).strip()  # nosec
            # node prints versions like v18.20.4
            m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", out)
            if m:
                major = int(m.group(1))
                print_success(f"✅ Node is installed: {out} ({node})")
                if major < NODE_MIN_MAJOR:
                    print_warning(
                        "⚠️ Your Node major version is <20 — some kits (e.g., NestJS) may require Node >=20."
                    )
                    print_info(
                        "Tip: use nvm/volta to switch Node versions, or run the kit smoke-tests in Docker to avoid local engine mismatches."
                    )
            else:
                print_info(f"ℹ️ Node is present but version couldn't be parsed: {out}")
        except subprocess.CalledProcessError:
            print_warning("⚠️ Failed to read Node version (node --version returned non-zero)")
    else:
        print_warning("⚠️ Node is not installed or not on PATH")
        print_info("Tip: install Node (nvm or volta recommended) or use Docker for Node-based kits")

    # Check for common package managers
    pms = {"npm": shutil.which("npm"), "yarn": shutil.which("yarn"), "pnpm": shutil.which("pnpm")}
    found_pm = [name for name, path in pms.items() if path]
    if found_pm:
        print_success(f"✅ Package manager(s) available: {', '.join(found_pm)}")
    else:
        print_warning("⚠️ No Node package manager found (npm/yarn/pnpm)")
        print_info(
            "Tip: install npm (comes with Node) or yarn/pnpm. Some kits will fail to init without a package manager."
        )

    # If package.json exists in the repo root or kits, warn about engine mismatches
    project_root = Path(__file__).resolve().parents[3]
    package_paths = list(project_root.rglob("package.json"))
    if package_paths:
        print_info(
            "Detected package.json files in repository — ensure your local Node and package-manager match kit 'engines' and lockfiles."
        )
