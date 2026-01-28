# cli/commands/doctor.py

import json
import re
import shutil
import subprocess  # nosec
import sys
from pathlib import Path

import typer

from ..ui.printer import print_error, print_info, print_success, print_warning

doctor_app = typer.Typer(help="🩺 Diagnose your development environment")

# Minimum supported Node major version for some kits (eg. NestJS)
NODE_MIN_MAJOR = 20


@doctor_app.command("check")
def check_env(
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
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

        kits_path = Path(__file__).parent.parent.parent / "kits"
        payload["kits"] = {
            "path": str(kits_path),
            "present": kits_path.exists(),
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
    kits_path = Path(__file__).parent.parent.parent / "kits"
    if kits_path.exists():
        print_success(f"✅ Kits directory found: {kits_path}")
    else:
        print_error("❌ Kits directory not found")

    # Check for at least one valid kit
    found_valid = False
    for kit in kits_path.iterdir():
        if kit.is_dir() and (kit / "kit.yaml").exists() and (kit / "generator.py").exists():
            found_valid = True
            break
    if found_valid:
        print_success("✅ At least one valid kit found")
    else:
        print_warning("⚠️ No valid kits found (kit.yaml or generator.py missing)")

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
