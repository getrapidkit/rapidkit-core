from pathlib import Path
from typing import Any, Dict, Optional

from cli.ui.printer import print_info, print_success, print_warning
from cli.utils.filesystem import create_file, resolve_project_path
from core.rendering.template_renderer import render_template
from core.services.module_path_resolver import resolve_module_directory


def ensure_init_files(destination_path: Path, project_root: Path) -> None:
    """Ensure all parent directories up to project root have __init__.py files."""
    current_dir = destination_path.parent
    while current_dir not in {project_root.parent, current_dir.parent}:
        # Do not create __init__.py at the project root itself
        if current_dir == project_root:
            break
        init_file = current_dir / "__init__.py"
        if not init_file.exists():
            try:
                init_file.touch()
                print_success(f"✅ Created: {init_file.relative_to(project_root)}")
            except (OSError, PermissionError) as e:
                print_warning(f"⚠️ Failed to create {init_file}: {e}")
        current_dir = current_dir.parent


def copy_extra_files(
    section: str,
    config: Dict[str, Any],
    project_root: Path,
    root_path: str,
    name: str,
    modules_path: Path,
    variables: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Copy files from sections like migrations, docs, ci_cd, etc.
    Render .j2 templates instead of copying them raw.
    """

    files = config.get(section, [])
    module_dir = resolve_module_directory(modules_path, name)

    def copy_or_render(
        src_path: Optional[Path],
        dest_path: Path,
        entry: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handles the actual copying or rendering of a file. If docs and no template, create empty or default doc."""
        if src_path and src_path.exists():
            if dest_path.exists():
                print_info(
                    f"⏭ Skipped existing {section} file: {dest_path.relative_to(project_root)}"
                )
                return
            try:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                ensure_init_files(dest_path, project_root)
                if src_path.suffix == ".j2":
                    content = render_template(src_path, variables or {})
                    create_file(dest_path, content)
                else:
                    dest_path.write_bytes(src_path.read_bytes())
                print_success(f"✅ Copied {section} file: {dest_path.relative_to(project_root)}")
            except (OSError, ValueError) as e:
                print_warning(f"⚠️ Failed to copy {section} file: {e}")
        elif section == "docs" and not src_path:
            # No template specified, create empty or default doc
            if dest_path.exists():
                print_info(
                    f"⏭ Skipped existing {section} file: {dest_path.relative_to(project_root)}"
                )
                return
            try:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                ensure_init_files(dest_path, project_root)
                doc_content = ""
                if entry and entry.get("description"):
                    doc_content = f"# {entry.get('description')}\n"
                create_file(dest_path, doc_content)
                print_success(f"✅ Created empty doc: {dest_path.relative_to(project_root)}")
            except (OSError, ValueError) as e:
                print_warning(f"⚠️ Failed to create doc {dest_path}: {e}")
        else:
            print_warning(f"⚠️ {section} file not found: {src_path}")

    def process_entry(entry: Any) -> None:
        """Validate and process a single file entry. Prefer template, fallback to path for docs."""
        rel_path = None
        template_file = None
        dest_file_name = None
        if isinstance(entry, dict):
            template_file = entry.get("template")
            rel_path = template_file or entry.get("path")
            dest_file_name = entry.get("path")
        else:
            rel_path = entry
        if not rel_path:
            print_warning(f"⚠️ Skipping {section} entry with no template or path: {entry}")
            return
        # If template is absolute (contains /), use it as is; else build path
        if template_file:
            src_path = module_dir / template_file
        else:
            # For docs, there may be no template, so src_path may not exist
            src_path = module_dir / "templates" / rel_path if section != "docs" else None
        # If dest_file_name is a directory-like path (e.g. tests/.../unit),
        # and we have a template, append the template basename (without .j2)
        dest_segment = dest_file_name or (Path(rel_path).with_suffix("") if rel_path else "")
        if isinstance(entry, dict) and template_file and dest_file_name:
            ds = str(dest_segment)
            if ds.endswith("/unit") or ds.endswith("/integration") or ds.endswith("/tests"):
                tmpl_base = Path(template_file).name
                if tmpl_base.endswith(".j2"):
                    tmpl_base = tmpl_base[:-3]
                dest_segment = Path(dest_segment) / tmpl_base
        dest_path = resolve_project_path(project_root, root_path, dest_segment)
        copy_or_render(src_path, dest_path, entry)

    if section == "ci_cd" and isinstance(files, dict):
        # ci_cd with nested sections like test, lint, etc.
        for sub_section in files.values():
            for entry in sub_section:
                process_entry(entry)
    else:
        # docs, migrations, or ci_cd as a flat list
        for entry in files:
            process_entry(entry)
