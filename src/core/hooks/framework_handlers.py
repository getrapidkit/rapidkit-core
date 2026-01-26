# src / core / hooks / framework_handlers.py
from pathlib import Path

from cli.ui.printer import print_info, print_success, print_warning


def handle_fastapi_router(rel_path: str, mount_path: Path) -> None:  # project_root removed
    if not mount_path.exists():
        print_warning(f"⚠️ Could not find {mount_path.name} to auto-mount router.")
        return

    import_path = rel_path.replace("/", ".").replace(".py", "")
    router_var = import_path.split(".")[-1]
    import_line = f"from {import_path} import router as {router_var}_router"
    include_line = f"app.include_router({router_var}_router)"

    content = mount_path.read_text()
    if import_line in content and include_line in content:
        print_info(f"🔁 Router already mounted: {router_var}")
        return

    content += f"\n\n{import_line}\n{include_line}\n"
    mount_path.write_text(content)
    print_success(f"✅ Mounted router {router_var} in {mount_path.name}")


def handle_nestjs_module(
    project_root: Path, rel_path: str, root_path: str
) -> None:  # keep signature (used elsewhere)
    """For NestJS, automatically update `app.module.ts` to include the new module."""
    app_module_path = project_root / root_path / "src/app.module.ts"
    if not app_module_path.exists():
        print_warning("⚠️ app.module.ts not found.")
        return

    stem = Path(rel_path).stem
    if stem.endswith(".module"):
        stem = stem[: -len(".module")]

    module_name_parts = stem.replace("-", "_").split("_")
    module_class = "".join(part.capitalize() for part in module_name_parts if part) + "Module"
    import_path = "./" + rel_path.replace(".ts", "").replace("\\", "/")

    content = app_module_path.read_text()
    if module_class in content:
        print_info(f"🔁 Module already imported: {module_class}")
        return

    import_line = f"import {{ {module_class} }} from '{import_path}';"
    updated_content = (
        import_line + "\n" + content.replace("imports: [", f"imports: [\n    {module_class},")
    )

    app_module_path.write_text(updated_content)
    print_success(f"✅ Registered {module_class} in app.module.ts")
