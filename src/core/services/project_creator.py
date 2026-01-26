# src / core / services / project_creator.py
import getpass
import shutil
import subprocess  # nosec - safe usage for controlled CLI commands
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.config.version import CURRENT_VERSION, check_min_version
from core.engine.registry import KitRegistry
from core.exceptions import RapidKitError, ValidationError
from core.services.project_metadata import ProjectMetadata, save_project_metadata


class ProjectCreatorService:
    def __init__(self) -> None:
        self.registry = KitRegistry()

    def _parse_variables(self, vars_list: Optional[List[str]]) -> Dict[str, str]:
        variables: Dict[str, str] = {}
        if vars_list:
            for var in vars_list:
                if "=" not in var:
                    raise ValidationError(f"Invalid variable format: '{var}'. Use key=value")
                key, value = var.split("=", 1)
                variables[key] = value
        return variables

    def _has_missing_required_variables(self, kit_config: Any, variables: Dict[str, Any]) -> bool:
        return any(var.required and var.name not in variables for var in kit_config.variables)

    def _get_run_command_for_kit(
        self, kit_name: str, variables: Optional[Dict[str, Any]] = None
    ) -> str:
        if kit_name.startswith("nestjs"):
            package_manager = str((variables or {}).get("package_manager", "npm")).lower()
            run_commands = {
                "npm": "npm run start:dev",
                "yarn": "yarn start:dev",
                "pnpm": "pnpm start:dev",
            }
            return run_commands.get(package_manager, "npm run start:dev")

        # FastAPI kits - prefer the RapidKit-friendly developer flow
        # Use `rapidkit dev` as the canonical developer run command. This
        # delegates to the project-local `.rapidkit/cli.py` or to Poetry as
        # appropriate, making the UX friendly for beginners.
        if kit_name.startswith("fastapi"):
            return "rapidkit dev"

        run_commands = {
            "fastapi.standard": "poetry run dev",
            "fastapi.ddd": "poetry run dev",
        }
        return run_commands.get(kit_name, "uvicorn src.main:app --reload")

    def _get_next_steps_for_kit(self, kit_name: str, variables: Dict[str, Any]) -> List[str]:
        activate_steps = [
            "source .rapidkit/activate",
            "rapidkit init",
            "./bootstrap.sh",
        ]
        if kit_name.startswith("nestjs"):
            steps = activate_steps.copy()
            steps.append(self._get_run_command_for_kit(kit_name, variables))
            return steps

        # For FastAPI projects share the activation/init/bootstrap flow before the run command
        if kit_name.startswith("fastapi"):
            steps = activate_steps.copy()
            steps.append(self._get_run_command_for_kit(kit_name, variables))
            return steps

        return [
            "poetry install",
            self._get_run_command_for_kit(kit_name, variables),
        ]

    def _install_essential_modules(
        self,
        project_path: Path,
        profile: str,
        print_info_func: Callable,
        print_success_func: Callable,
        print_error_func: Callable,
    ) -> None:
        """Install essential modules for the project."""
        rapidkit_exe: Optional[str] = None

        # Prefer the currently-running console script path.
        try:
            argv0 = Path(sys.argv[0])
            if argv0.name == "rapidkit" and argv0.exists():
                rapidkit_exe = str(argv0)
        except (OSError, ValueError):
            rapidkit_exe = None

        # Then prefer the venv's bin/rapidkit (works even if sys.executable resolves to /usr/bin).
        if rapidkit_exe is None:
            venv_candidate = Path(sys.prefix) / "bin" / "rapidkit"
            if venv_candidate.exists():
                rapidkit_exe = str(venv_candidate)

        # Finally, fall back to PATH.
        if rapidkit_exe is None:
            rapidkit_exe = shutil.which("rapidkit")

        if not rapidkit_exe:
            raise RapidKitError(
                "Cannot install essential modules because 'rapidkit' executable was not found. "
                "Activate your environment or ensure RapidKit is installed."
            )

        essential_modules = [
            "free/essentials/settings",
            "free/essentials/logging",
            "free/essentials/deployment",
            "free/essentials/middleware",
        ]

        print_info_func("\n🔧 Installing essential modules...")

        failed_modules: List[str] = []

        for module in essential_modules:
            print_info_func(f"📦 Installing {module}...")

            # Call the rapidkit CLI command directly
            cmd = [
                rapidkit_exe,
                "add",
                "module",
                module,
                "--profile",
                profile,
                "--project",
                str(project_path),
                "--force",
            ]

            try:
                result = subprocess.run(  # nosec - safe controlled command execution
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=str(project_path),
                    timeout=300,  # 5 minute timeout
                    check=False,  # We handle return code manually
                )
            except subprocess.TimeoutExpired:
                print_error_func(f"❌ Timeout installing {module}")
                failed_modules.append(module)
                continue
            except Exception as e:  # noqa: BLE001 - CLI failures should not abort project creation
                print_error_func(f"❌ Error installing {module}: {e}")
                failed_modules.append(module)
                continue

            if result.returncode == 0:
                print_success_func(f"✅ {module} installed successfully")
                continue

            details = (result.stderr or result.stdout or "").strip()
            if details:
                print_error_func(f"❌ Failed to install {module}: {details}")
            else:
                print_error_func(f"❌ Failed to install {module} (no output)")
            failed_modules.append(module)

        if failed_modules:
            print_error_func(
                f"❌ Some essential modules failed to install: {', '.join(failed_modules)}"
            )

    def _get_kit_profile(self, kit_name: str) -> str:
        """Get the profile name for a kit (e.g., 'fastapi/standard' from 'fastapi.standard')."""
        return kit_name.replace(".", "/")

    def _apply_kit_defaults(self, kit_config: Any, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Merge kit variable defaults into the active variables map without overriding explicit values."""
        merged = variables.copy()
        for var in getattr(kit_config, "variables", []):
            if var.name in merged:
                continue
            default_value = getattr(var, "default", None)
            if default_value is not None:
                merged[var.name] = default_value
        return merged

    def create_project(
        self,
        kit_name: str,
        project_name: str,
        output_dir: Path,
        variables: Optional[Dict[str, Any]] = None,
        force: bool = False,
        interactive: bool = False,
        debug: bool = False,
        prompt_func: Optional[Callable[..., Any]] = None,
        print_funcs: Optional[Dict[str, Callable[..., Any]]] = None,
        install_essential_modules: bool = True,
    ) -> List[Path]:
        # Set default print funcs
        if print_funcs:
            print_info_func = print_funcs.get("info", print)
            print_error_func = print_funcs.get("error", print)
            print_success_func = print_funcs.get("success", print)
        else:
            # Explicitly type the default print functions
            def _p(msg: Any) -> None:
                print(msg)

            print_info_func = _p
            print_error_func = _p
            print_success_func = _p

        variables = variables or {}
        kit_name = kit_name.replace(" ", ".").lower()

        if kit_name not in self.registry.list_kits_names():
            available = self.registry.list_kits_names()
            print_error_func(f"Kit '{kit_name}' not found.")
            print_info_func("Available kits:")
            for k in available:
                print_info_func(f"  • {k}")
            raise RapidKitError(f"Kit '{kit_name}' not found.")

        kit_config = self.registry.get_kit(kit_name)
        check_min_version(kit_config.min_rapidkit_version, CURRENT_VERSION)

        print_info_func(f"Using kit: {kit_config.display_name}")
        print_info_func(f"Description: {kit_config.description}")

        variables.setdefault("project_name", project_name)
        variables.setdefault("year", str(datetime.now().year))
        variables.setdefault("author", getpass.getuser())
        variables.setdefault("dependencies", {"external": []})
        variables.setdefault(
            "secrets",
            {
                "SECRET_KEY": "supersecurekey",
                "DATABASE_URL": "postgresql://user:password@prod-db:5432/prod_db",
                "MONGODB_URL": "mongodb://prod-db:27017",
            },
        )

        variables = self._apply_kit_defaults(kit_config, variables)

        # Ensure programmatic callers who pass install_essential_modules=False
        # do not end up with kit-defaults that enable essential modules.
        # CLI path already ensures these variables are set based on the prompt
        # but callers of ProjectCreatorService.create_project directly must
        # also be respected.
        if install_essential_modules is False:
            # Only overwrite missing values — do not override explicit caller intent
            variables.setdefault("install_settings", False)
            variables.setdefault("install_logging", False)
            variables.setdefault("install_deployment", False)

        if interactive or self._has_missing_required_variables(kit_config, variables):
            if not prompt_func:
                raise RuntimeError("Interactive mode requires prompt_func callable")
            # prompt_func expected to return updated variables mapping
            variables = prompt_func(kit_config, variables, interactive=interactive)

        output_path = output_dir.resolve() / project_name

        # For development environment, use boilerplates subdirectory
        # Check if we're in a development environment by looking for src/ directory
        if (output_dir.resolve().parent / "src").exists():
            output_path = output_dir.resolve() / "boilerplates" / project_name

        if output_path.exists() and not force:
            raise RapidKitError(f"Directory '{output_path}' exists and force is not set.")

        print_info_func("Generating project files...")

        generator = self.registry.get_generator(kit_name)
        vars_for_generate: Dict[str, Any] = variables or {}
        if debug:
            print_info_func("  [debug] Resolved variables:")
            for key, value in vars_for_generate.items():
                print_info_func(f"    - {key}: {value}")
        created_files_list = generator.generate(output_path, vars_for_generate)

        profile = self._get_kit_profile(kit_name)
        metadata = ProjectMetadata.create(
            kit_name=kit_name, profile=profile, rapidkit_version=str(CURRENT_VERSION)
        )
        try:
            save_project_metadata(output_path, metadata)
        except (
            OSError,
            ValueError,
        ) as exc:  # pragma: no cover - metadata failure shouldn't block project creation
            print_error_func(f"⚠️ Failed to persist project metadata: {exc}")

        if install_essential_modules:
            self._install_essential_modules(
                output_path, profile, print_info_func, print_success_func, print_error_func
            )
        else:
            print_info_func("Skipping essential module installation by user choice.")

        print_success_func("Project created successfully!")
        print_info_func(f"Location: {output_path}")
        print_info_func("Next steps:")
        print_info_func(f"  cd {project_name}")
        for step in self._get_next_steps_for_kit(kit_name, vars_for_generate):
            print_info_func(f"  {step}")
        # generator returns List[str] (file paths); convert to List[Path]
        return [Path(p) for p in created_files_list]
