import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import typer
from typer.models import ArgumentInfo, OptionInfo
from typing_extensions import Annotated

from core.exceptions import ValidationError
from core.services.module_structure_validator import (
    ModuleStructureError,
    ensure_module_structure,
)
from core.services.project_creator import ProjectCreatorService

from ..ui.printer import print_error, print_info, print_success, print_warning
from ..utils.module_scaffold import ModuleScaffolder
from ..utils.prompts import prompt_variables
from ..utils.validators import validate_project_name


def _format_kit_choice(slug: str) -> str:
    """Convert a kit slug like 'fastapi.standard' into 'fastapi[standard]' for display."""
    if "." in slug:
        family, variant = slug.split(".", 1)
        return f"{family}[{variant}]"
    return slug


def _collect_available_kits(
    service: ProjectCreatorService,
) -> Tuple[List[Tuple[str, str]], Dict[str, str]]:
    """Return sorted kit choices and lookup mapping for interactive selection."""
    configs = {cfg.name.lower(): cfg for cfg in service.registry.list_kits()}
    sorted_choices = sorted(
        ((slug, cfg.display_name) for slug, cfg in configs.items()), key=lambda item: item[0]
    )
    slug_lookup = {slug.lower(): slug for slug in service.registry.list_kits_names()}
    # Ensure canonical names are available even if not explicitly returned by list_kits_names
    for slug in configs:
        slug_lookup.setdefault(slug.lower(), slug)
    return sorted_choices, slug_lookup


def _prompt_for_kit(service: ProjectCreatorService) -> str:
    choices, slug_lookup = _collect_available_kits(service)
    if not choices:
        print_error("❌ No kits are available to scaffold.")
        raise typer.Exit(code=1)

    print_info("\nSelect a kit to scaffold:")
    for idx, (slug, display_name) in enumerate(choices, start=1):
        pretty = _format_kit_choice(slug)
        subtitle = f" — {display_name}" if display_name else ""
        print_info(f"  [{idx}] {pretty}{subtitle}")

    while True:
        answer = typer.prompt("Enter kit number or name").strip().lower()
        if not answer:
            print_warning("Please choose a kit from the list.")
            continue

        if answer.isdigit():
            index = int(answer)
            if 1 <= index <= len(choices):
                selected_slug = choices[index - 1][0]
                print_success(f"Selected kit: {selected_slug}")
                return selected_slug
            print_warning(f"Select a number between 1 and {len(choices)}.")
            continue

        matched_slug = slug_lookup.get(answer)
        if matched_slug:
            print_success(f"Selected kit: {matched_slug}")
            return matched_slug

        print_warning("Invalid selection. Try again using the number or kit name shown above.")


def _prompt_for_project_name() -> str:
    while True:
        name = cast(str, typer.prompt("Project name")).strip()
        try:
            validate_project_name(name)
        except ValidationError as exc:
            print_warning(str(exc))
            continue
        return name


def _prompt_for_package_manager() -> str:
    choices = ["npm", "yarn", "pnpm"]
    print_info("\nSelect a package manager:")
    for idx, option in enumerate(choices, start=1):
        print_info(f"  [{idx}] {option}")

    while True:
        answer = cast(str, typer.prompt("Enter package manager (name or number)")).strip().lower()
        if not answer:
            print_warning("Please choose one of the available package managers.")
            continue

        if answer.isdigit():
            index = int(answer)
            if 1 <= index <= len(choices):
                selected = choices[index - 1]
                print_success(f"Selected package manager: {selected}")
                return selected
            print_warning(f"Select a number between 1 and {len(choices)}.")
            continue

        if answer in choices:
            print_success(f"Selected package manager: {answer}")
            return answer

        print_warning("Invalid selection. Try again using the number or name shown above.")


def _detect_package_manager() -> str:
    """Best-effort pick a Node package manager for non-interactive runs."""
    for pm in ("pnpm", "yarn", "npm"):
        if shutil.which(pm):
            return pm
    return "npm"


create_app = typer.Typer()


@create_app.callback(invoke_without_command=True)
def create_callback(ctx: typer.Context) -> None:
    """Default to interactive project scaffolding when no subcommand is passed."""

    if ctx.invoked_subcommand is None:
        print_info("Launching interactive project scaffolding…")
        ctx.invoke(create_project)


@create_app.command("project")
def create_project(
    kit_name: Optional[str] = typer.Argument(None, help="Kit template name"),
    project_name: Optional[str] = typer.Argument(None, help="Name of the project to create"),
    output: Optional[Path] = None,  # will be set inside
    variable: Optional[List[str]] = None,  # will be set inside
    interactive: bool = typer.Option(False, "--interactive", help="Enable interactive mode"),
    install_essentials: Annotated[
        Optional[bool],
        typer.Option(
            "--install-essentials/--skip-essentials",
            help="Control installation of essential modules after scaffolding",
        ),
    ] = None,
    force: bool = typer.Option(False, "--force", help="Force overwrite existing files"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
) -> None:
    """Create a new project from a kit template."""

    # Set default Options here to avoid B008
    if output is None:
        output = Path(".")
    if variable is None:
        variable = []

    try:
        kit_name_obj: object = kit_name
        if isinstance(kit_name_obj, ArgumentInfo):
            kit_name = None
        else:
            kit_name = cast(Optional[str], kit_name_obj)

        project_name_obj: object = project_name
        if isinstance(project_name_obj, ArgumentInfo):
            project_name = None
        else:
            project_name = cast(Optional[str], project_name_obj)

        service = ProjectCreatorService()

        interactive_raw: Any = interactive
        if isinstance(interactive_raw, OptionInfo):
            interactive = bool(interactive_raw.default)
        else:
            interactive = bool(interactive_raw)

        kit_name_initially_provided = kit_name is not None
        project_name_initially_provided = project_name is not None

        if kit_name is None:
            kit_name = _prompt_for_kit(service)

        if project_name is None:
            project_name = _prompt_for_project_name()

        validate_project_name(project_name)
        variables: Dict[str, Any] = {}
        for var in variable:
            if "=" not in var:
                print_error(f"Invalid variable format: '{var}'. Use key=value")
                raise typer.Exit(code=1)
            key, value = var.split("=", 1)
            variables[key] = value

        normalized_kit = kit_name.lower()
        if normalized_kit.startswith("nestjs") and "package_manager" not in variables:
            should_prompt_pm = (
                interactive
                or not kit_name_initially_provided
                or not project_name_initially_provided
            )
            if should_prompt_pm:
                variables["package_manager"] = _prompt_for_package_manager()
            else:
                variables["package_manager"] = _detect_package_manager()
                print_info(
                    f"Selected package manager (non-interactive): {variables['package_manager']}"
                )

        raw_install_essentials = cast(bool | None | OptionInfo, install_essentials)
        if isinstance(raw_install_essentials, OptionInfo):
            install_essentials = cast(Optional[bool], raw_install_essentials.default)
        else:
            install_essentials = raw_install_essentials

        # The CLI will pass a bool or None for this option at runtime;
        # treat None as "unset" and decide whether to prompt the user.
        if install_essentials is None:
            should_prompt = (
                interactive
                or not kit_name_initially_provided
                or not project_name_initially_provided
            )
            if should_prompt:
                install_essentials = typer.confirm(
                    "\nInstall essential modules (settings, logging, deployment, middleware)?",
                    default=True,
                )
            else:
                install_essentials = True

        # Ensure kit variables reflect the essential module choice unless explicitly provided
        if "install_settings" not in variables:
            variables["install_settings"] = bool(install_essentials)
        if "install_logging" not in variables:
            variables["install_logging"] = bool(install_essentials)
        if "install_deployment" not in variables:
            variables["install_deployment"] = bool(install_essentials)

        created_files = service.create_project(
            kit_name=kit_name,
            project_name=project_name,
            output_dir=output,
            variables=variables,
            force=force,
            interactive=interactive,
            debug=debug,
            prompt_func=prompt_variables,
            print_funcs={
                "info": print_info,
                "error": print_error,
                "success": print_success,
                "warning": print_warning,
            },
            install_essential_modules=install_essentials,
        )
        if created_files:
            print_info("\nFiles created:")
            for f in created_files:
                print_success(f"  + {f}")

    except (ValueError, OSError, RuntimeError) as e:
        if debug:
            raise
        print_error(f"Error: {e}")
        raise typer.Exit(code=1) from None


@create_app.command("module")
def create_module_command(
    name: Annotated[str, typer.Argument(help="Module name (snake-case)")],
    category: Annotated[
        str,
        typer.Option("--category", "-c", help="Category path under the tier"),
    ] = "core",
    tier: Annotated[
        str,
        typer.Option("--tier", "-t", help="Module tier (free, enterprise, ...)"),
    ] = "free",
    description: Annotated[
        Optional[str],
        typer.Option("--description", "-d", help="Optional description for README"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(False, "--force", help="Overwrite existing files"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(False, "--dry-run", help="Preview files without writing to disk"),
    ] = False,
) -> None:
    """Scaffold a lean RapidKit module."""

    scaffolder = ModuleScaffolder()
    try:
        result = scaffolder.create_module(
            tier=tier,
            category=category,
            module_name=name,
            description=description,
            force=force,
            dry_run=dry_run,
        )
    except ValueError as exc:
        print_error(f"❌ {exc}")
        raise typer.Exit(code=1) from None

    repo_root = Path(__file__).resolve().parents[3]

    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(repo_root))
        except ValueError:
            return str(path)

    def _emit(label: str, paths: List[Path], printer: Callable[[str], None]) -> None:
        if not paths:
            return
        printer(f"{label} ({len(paths)}):")
        for item in sorted(paths):
            printer(f"  - {_rel(item)}")

    if dry_run:
        print_info("Dry run — planned scaffold (no files written):")
        _emit("Would create", result.created_files, print_info)
        _emit("Would overwrite", result.overwritten_files, print_info)
        _emit("Would skip", result.skipped_files, print_info)
        return

    _emit("Created", result.created_files, print_success)
    _emit("Overwritten", result.overwritten_files, print_warning)
    _emit("Skipped", result.skipped_files, print_warning)

    module_slug = result.context.get("module_slug", f"{tier}/{category}/{name}")
    if not module_slug:
        module_slug = f"{tier}/{category}/{name}"

    if not dry_run:
        try:
            ensure_module_structure(module_slug)
        except ModuleStructureError as exc:
            print_error("❌ Module structure validation failed:")
            for line in str(exc).splitlines():
                print_error(f"  {line}")
            raise typer.Exit(code=1) from None

    module_import_path = result.context.get("module_import_path")
    module_dir = _rel(result.module_path)

    print_info(f"\n📁 Module scaffold ready at: {module_dir}")
    print_info("Next steps:")
    print_info("  • Review module.yaml metadata and adjust compatibility/testing sections.")
    print_info("  • Define snippet bundles in config/snippets.yaml for reusable inserts.")
    print_info("  • Flesh out the templates under templates/ for your runtimes.")
    if module_import_path:
        print_info(
            "  • Smoke-test generator: poetry run python -m "
            f"{module_import_path}.generate fastapi ./tmp/{name}"
        )
    print_info(
        '  • Validate structure: poetry run python -c "from core.services.module_structure_validator '
        f"import ensure_module_structure; ensure_module_structure('{module_slug}')\""
    )
