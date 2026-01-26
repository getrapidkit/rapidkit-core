"""Hooks for the NestJS Standard Kit."""

import getpass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from kits.shared import ensure_settings_vendor_snapshot


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

        # Prefer the rapidkit flow (creates local launcher and handles deps)
        print("\n📝 Next steps:")
        print(f"1. cd {project_name}")
        print("2. source .rapidkit/activate")
        print("3. rapidkit init")
        print("4. ./bootstrap.sh")
        print("5. rapidkit dev")

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

    # Optionally generate a package lock (package-lock.json / pnpm-lock.yaml / yarn.lock)
    try:
        import os
        import subprocess  # nosec - safe use for lock generation

        def _is_truthy(value: object) -> bool:
            return str(value).lower() in {"1", "true", "yes", "on"}

        env_toggle = os.environ.get("RAPIDKIT_GENERATE_LOCKS")
        if env_toggle is not None:
            should_lock = _is_truthy(env_toggle)
        elif _is_truthy(os.environ.get("RAPIDKIT_SKIP_LOCKS", "0")):
            should_lock = False
        elif variables and "generate_lock" in variables:
            should_lock = bool(variables.get("generate_lock", True))
        else:
            should_lock = True

        if should_lock and output_path:
            pm = variables.get("package_manager", "npm") if variables else "npm"
            print(f"\nℹ️ Generating lockfile for package manager: {pm}")
            if pm == "npm":
                subprocess.run(
                    ["npm", "install", "--package-lock-only"], cwd=str(output_path), check=False
                )  # nosec - safe static invocation of npm
            elif pm == "pnpm":
                subprocess.run(
                    ["pnpm", "install", "--lockfile-only"], cwd=str(output_path), check=False
                )  # nosec - safe static invocation of pnpm
            elif pm == "yarn":
                subprocess.run(
                    ["yarn", "install", "--mode=update-lockfile"], cwd=str(output_path), check=False
                )  # nosec - safe static invocation of yarn
            print("ℹ️ Lockfile generation attempted (check output above).")
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        print("WARN: Lockfile generation attempted and failed. Continuing without locking.")
