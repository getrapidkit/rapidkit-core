"""Hooks for the NestJS Standard Kit."""

import getpass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from kits.shared import (
    attempt_lockfile_generation,
    ensure_settings_vendor_snapshot,
    should_generate_lockfile,
)


def pre_generate(variables: Dict[str, Any]) -> None:
    """Validate and normalize variables before project scaffolding."""
    print("🚀 Running pre_generate hook for NestJS Standard Kit")

    if not variables.get("author"):
        variables["author"] = getpass.getuser()

    if not variables.get("year"):
        variables["year"] = str(datetime.now().year)

    project_name = variables.get("project_name", "")
    normalized = project_name.replace("-", "").replace("_", "")
    if not normalized or not normalized.isalnum():
        raise ValueError(
            "Project name should contain only letters, numbers, hyphens, and underscores"
        )

    package_manager = variables.get("package_manager", "npm")
    if package_manager not in {"npm", "yarn", "pnpm"}:
        raise ValueError("package_manager must be one of: npm, yarn, pnpm")

    if variables.get("database_type") == "sqlite" and variables.get("auth_type") == "oauth2":
        raise ValueError(
            "SQLite is not recommended for OAuth2 features. Consider using PostgreSQL or MySQL."
        )

    print(f"✅ Pre-generation validation completed for: {project_name}")


def post_generate(
    output_path: Optional[Path] = None, variables: Optional[Dict[str, Any]] = None
) -> None:
    """Provide next steps after the project is generated."""
    print("\n" + "=" * 60)
    print("🎉 NestJS Standard Kit generated successfully!")
    print("=" * 60)

    vendor_dir: Optional[Path] = None
    if output_path:
        try:
            vendor_dir = ensure_settings_vendor_snapshot(output_path, framework="nestjs")
        except RuntimeError as exc:
            print(f"⚠️  Failed to sync settings vendor snapshot: {exc}")
        else:
            try:
                rel_vendor = vendor_dir.relative_to(output_path)
            except ValueError:
                rel_vendor = vendor_dir
            print(f"📦 Settings vendor synced: {rel_vendor}")

    if variables:
        project_name = variables.get("project_name", "nestjs-app")
        package_manager = variables.get("package_manager", "npm")
        auth_type = variables.get("auth_type", "jwt")
        database_type = variables.get("database_type", "postgresql")

        print(f"📁 Project: {project_name}")
        print(f"🔐 Auth: {auth_type}")
        print(f"🗄️  Database: {database_type}")
        print(f"📦 Package manager: {package_manager}")

        commands = {
            "npm": ["npm install", "npm run start:dev"],
            "yarn": ["yarn install", "yarn start:dev"],
            "pnpm": ["pnpm install", "pnpm start:dev"],
        }
        install_cmd, dev_cmd = commands.get(package_manager, commands["npm"])

        # Prefer the Workspai/RapidKit Core flow (creates local launcher and handles deps)
        print("\n📝 Next steps:")
        print(f"1. cd {project_name}")
        print("2. source .rapidkit/activate  # loads the project-local RapidKit Core launcher")
        print("3. rapidkit init              # project bootstrap")
        print("4. ./bootstrap.sh")
        print("5. rapidkit dev               # project runtime")
        print("\nWorkspace intelligence:")
        print("  • From the workspace root, run: npx workspai workspace model --json")

        # Also include the raw package-manager steps as an alternate path for users
        print("\nOr, if you prefer to manage deps directly using your package manager:")
        print(f"  • {install_cmd}")
        print("  • cp .env.example .env")
        print("  • # Update .env values")
        print(f"  • {dev_cmd}")

        if variables.get("docker_support", True):
            print("\n🐳 Docker commands:")
            print("   docker-compose up -d")
            print("   docker-compose down")

        features = []
        if variables.get("include_monitoring"):
            features.append("📊 Monitoring")
        if variables.get("include_caching"):
            features.append("🔴 Redis")
        if variables.get("include_logging"):
            features.append("📝 Logging")
        if variables.get("include_testing"):
            features.append("🧪 Testing")
        if variables.get("include_docs"):
            features.append("📚 Documentation")

        if features:
            print("\n✨ Features enabled: " + ", ".join(features))

    if output_path:
        print(f"\n📂 Project location: {output_path}")

    print("\n📚 Documentation: docs/README.md")
    print("=" * 60)

    if should_generate_lockfile(variables) and output_path:
        pm = str(variables.get("package_manager", "npm") if variables else "npm")
        lock_commands = {
            "npm": (["npm", "install", "--package-lock-only"], "package-lock.json"),
            "pnpm": (["pnpm", "install", "--lockfile-only"], "pnpm-lock.yaml"),
            "yarn": (["yarn", "install", "--mode=update-lockfile"], "yarn.lock"),
        }
        command, label = lock_commands.get(pm, lock_commands["npm"])
        attempt_lockfile_generation(output_path=output_path, command=command, label=label)
