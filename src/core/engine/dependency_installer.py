# src / core / engine / dependency_installer.py

import json
import os
import re
import subprocess
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from cli.ui.printer import print_info, print_success, print_warning
from cli.utils.filesystem import find_project_root
from core.services.poetry_dependency_normalizer import normalize_poetry_dependencies
from core.services.profile_utils import profile_aliases, resolve_profile_chain
from core.services.snippet_injector import (
    filter_and_update_poetry_dependencies_snippet,
    parse_poetry_dependency_line,
)


def _sync_poetry_lockfile(project_root: Path) -> None:
    """Sync poetry.lock with pyproject.toml.

    Stabilization relies on `poetry check --lock` and `poetry install --sync` for
    deterministic installs. If module installation mutates pyproject.toml without
    updating poetry.lock, deterministic stabilization will fail. This function
    fail-closes for Poetry projects.
    """

    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return

    lock_path = project_root / "poetry.lock"
    if not lock_path.exists():
        return

    # Poetry 2.x defaults to preserving already-locked versions.
    # (The old `--no-update` flag is not available.)
    cmd = ["poetry", "lock", "--no-interaction"]
    env = dict(os.environ)
    # Prevent secretstorage-backed keyring usage on headless agents.
    env.setdefault("PYTHON_KEYRING_BACKEND", "keyring.backends.null.Keyring")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "poetry is required to sync poetry.lock after dependency injection, "
            "but it was not found on PATH."
        ) from exc

    if result.returncode != 0:
        raise RuntimeError(
            "poetry lock sync failed (poetry.lock is out of date).\n"
            f"Command: {' '.join(cmd)}\n"
            f"cwd: {project_root}\n\n"
            f"stdout:\n{result.stdout}\n\n"
            f"stderr:\n{result.stderr}\n"
        )

    print_success(f"🔒 Synced {lock_path}")


def _sync_npm_lockfile(project_root: Path) -> None:
    """Sync package-lock.json with package.json.

    We rely on `npm ci` for deterministic installs during stabilization.
    If module installation mutates package.json without updating the lockfile,
    `npm ci` will fail. This function fail-closes for Node projects.
    """

    package_json_path = project_root / "package.json"
    if not package_json_path.exists():
        return

    package_lock_path = project_root / "package-lock.json"
    yarn_lock_path = project_root / "yarn.lock"
    pnpm_lock_path = project_root / "pnpm-lock.yaml"

    if not package_lock_path.exists() and (yarn_lock_path.exists() or pnpm_lock_path.exists()):
        print_warning(
            "⚠️ Detected yarn/pnpm lockfile without package-lock.json; skipping npm lockfile sync."
        )
        return

    cmd = [
        "npm",
        "install",
        "--package-lock-only",
        "--ignore-scripts",
        "--no-audit",
        "--fund=false",
    ]
    env = dict(os.environ)
    env.setdefault("NPM_CONFIG_UPDATE_NOTIFIER", "false")
    env.setdefault("NPM_CONFIG_AUDIT", "false")
    env.setdefault("NPM_CONFIG_FUND", "false")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "npm is required to sync package-lock.json after dependency injection, "
            "but it was not found on PATH."
        ) from exc

    if result.returncode != 0:
        raise RuntimeError(
            "npm lockfile sync failed (package-lock.json is out of date).\n"
            f"Command: {' '.join(cmd)}\n"
            f"cwd: {project_root}\n\n"
            f"stdout:\n{result.stdout}\n\n"
            f"stderr:\n{result.stderr}\n"
        )

    if package_lock_path.exists():
        print_success(f"🔒 Synced {package_lock_path}")


def _collect_external(deps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [dep for dep in deps if dep.get("source") == "external"]


def _split_name_extras(raw_name: object) -> tuple[str, List[str]]:
    """Split dependency identifier into package name and extras list."""

    if not isinstance(raw_name, str):
        return "", []
    if "[" not in raw_name or not raw_name.endswith("]"):
        return raw_name, []
    base, extras_part = raw_name.split("[", 1)
    extras_part = extras_part[:-1]  # drop trailing ']'
    extras = [segment.strip() for segment in extras_part.split(",") if segment.strip()]
    return base or raw_name, extras


def _format_extras(extras: Iterable[str]) -> str:
    return ", ".join(f'"{extra}"' for extra in extras if extra)


def _format_poetry_dependency(dep: Dict[str, Any]) -> Optional[str]:
    """Return a Poetry dependency line supporting extras and inline tables."""

    raw_name = dep.get("name")
    if not isinstance(raw_name, str):
        return None
    version = dep.get("version")
    if not isinstance(version, str) or not version.strip():
        return None

    base_name, inferred_extras = _split_name_extras(raw_name)
    declared_extras_raw = dep.get("extras")
    declared_extras: List[str]
    if isinstance(declared_extras_raw, (list, tuple)):
        declared_extras = [str(item).strip() for item in declared_extras_raw if str(item).strip()]
    elif isinstance(declared_extras_raw, str) and declared_extras_raw.strip():
        declared_extras = [declared_extras_raw.strip()]
    else:
        declared_extras = []

    extras = list(dict.fromkeys(inferred_extras + declared_extras))

    if extras:
        extras_literal = _format_extras(extras)
        return f'{base_name} = {{ version = "{version}", extras = [{extras_literal}] }}'

    return f'{base_name} = "{version}"'


def _extract_installed_slugs(payload: Any) -> List[str]:
    if not isinstance(payload, list):
        return []
    slugs: List[str] = []
    for entry in payload:
        if isinstance(entry, str):
            slugs.append(entry)
        elif isinstance(entry, dict):
            slug = entry.get("slug") or entry.get("module") or entry.get("name")
            if isinstance(slug, str) and slug:
                slugs.append(slug)
    return slugs


def install_module_dependencies(
    config: Dict[str, Any], profile: str, project: str, final: bool
) -> None:
    """
    Inject external dependencies into requirements.txt or pyproject.toml
    and check internal modules in registry.json. Dev dependencies are applied
    only when final == False.
    """
    depends_on_all = config.get("depends_on", {})
    if not isinstance(depends_on_all, dict):  # defensive
        depends_on_all = {}
    resolved_profiles = resolve_profile_chain(profile, config) if isinstance(config, dict) else []
    if not resolved_profiles:
        resolved_profiles = [profile]

    profile_lookup_chain: List[str] = []
    for resolved_profile in resolved_profiles:
        for alias in profile_aliases(resolved_profile):
            if alias not in profile_lookup_chain:
                profile_lookup_chain.append(alias)

    depends_on_profile: List[Dict[str, Any]] = []
    for resolved_profile in profile_lookup_chain:
        entries = depends_on_all.get(resolved_profile, [])
        if isinstance(entries, list):
            depends_on_profile.extend(entries)
    dev_deps_raw = config.get("dev_dependencies", []) if not final else []
    if not isinstance(dev_deps_raw, list):
        dev_deps_raw = []

    target_field = "__dependency_target"
    dependencies: List[Dict[str, Any]] = []
    for entry in depends_on_profile:
        if isinstance(entry, dict):
            dep = dict(entry)
            dep[target_field] = "prod"
            dependencies.append(dep)
    for entry in dev_deps_raw:
        if isinstance(entry, dict):
            dep = dict(entry)
            dep[target_field] = "dev"
            dependencies.append(dep)

    npm_deps = [dep for dep in dependencies if dep.get("tool") == "npm"]

    project_root = find_project_root(project)
    if project_root is None:
        print_warning("⚠️ Could not resolve project root; skipping dependency install")
        return
    registry_path = project_root / "registry.json"

    # Load registry
    try:
        registry = (
            json.loads(registry_path.read_text())
            if registry_path.exists()
            else {"installed_modules": []}
        )
        installed_modules = _extract_installed_slugs(registry.get("installed_modules", []))
    except (OSError, UnicodeDecodeError, JSONDecodeError) as e:
        print_warning(f"⚠️ Failed to read registry: {e}")
        installed_modules = []

    # External deps
    external_deps = _collect_external(dependencies)

    # Known dev-only tooling packages that should not be injected into main runtime deps
    dev_tool_names = {
        "black",
        "flake8",
        "pytest",
        "pytest-asyncio",
        "isort",
        "mypy",
        "ruff",
        "coverage",
        "pre-commit",
    }

    pyproject_file: Optional[Path] = project_root / "pyproject.toml"
    package_json_path = project_root / "package.json"
    is_node_project = package_json_path.exists()

    # Heuristic: if the project clearly has package.json we should treat it
    # as a Node project and avoid touching pyproject.toml. Some projects (or
    # previously mis-applied modules) can leave an accidental pyproject file
    # behind — do not corrupt it by injecting non-Python dependencies.
    if is_node_project:
        # There is a package.json: assume Node project and skip poetry injects
        print_warning(
            "⚠️ Detected package.json in project — skipping Poetry (pyproject.toml) dependency injection to avoid corrupting Node projects."
        )
        # still continue to validate internal modules but don't update pyproject
        pyproject_file = None

    if external_deps:
        # We now rely on full sync from pyproject -> requirements after pyproject update.
        # (Previous incremental requirements merge removed for canonical single-source-of-truth.)

        pyproject_changed = False

        # -------- pyproject.toml (Poetry) --------
        formatted_lines: List[str] = []
        for dep in external_deps:
            raw_name = dep.get("name")
            if raw_name in dev_tool_names:
                continue
            formatted = _format_poetry_dependency(dep)
            if formatted:
                # Only suppress dev tooling when targeting runtime dependencies; allow
                # dev_dependencies to inject test tooling (e.g., pytest-asyncio).
                target = dep.get(target_field)
                if target == "prod" and raw_name in dev_tool_names:
                    continue
                formatted_lines.append(formatted)
        snippet_poetry = "\n".join(formatted_lines)
        if snippet_poetry and pyproject_file:
            try:
                new_content = filter_and_update_poetry_dependencies_snippet(
                    pyproject_file, snippet_poetry
                )
                current = (
                    pyproject_file.read_text(encoding="utf-8")
                    if (pyproject_file and pyproject_file.exists())
                    else ""
                )
                if new_content != current:
                    pyproject_file.write_text(new_content, encoding="utf-8")
                    print_success(f"✅ Updated {pyproject_file}")
                    pyproject_changed = True
            except (OSError, ValueError) as e:
                print_warning(f"⚠️ Failed to update {pyproject_file}: {e}\n")

        # Always attempt normalization (moves dev tools, removes duplicates)
        try:
            if pyproject_file and normalize_poetry_dependencies(pyproject_file):
                print_success("🔧 Normalized Poetry dependency sections (dev tools moved)")
                pyproject_changed = True
        except (OSError, ValueError, RuntimeError) as e:
            print_warning(f"⚠️ Failed to normalize poetry dependencies: {e}")

        if pyproject_changed and pyproject_file:
            _sync_poetry_lockfile(project_root)
        # NOTE: Removed requirements.txt sync - using Poetry as single source of truth
        # Poetry workflow doesn't need requirements.txt files

    if npm_deps:
        if not is_node_project:
            print_warning(
                "⚠️ Module declared npm dependencies but no package.json was found; skipping injection."
            )
        else:
            try:
                package_payload = json.loads(package_json_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, JSONDecodeError) as exc:
                print_warning(f"⚠️ Failed to read {package_json_path}: {exc}")
            else:
                if not isinstance(package_payload, dict):
                    print_warning(
                        f"⚠️ package.json at {package_json_path} is not a JSON object; skipping npm dependency injection."
                    )
                else:
                    changed = False
                    for dep in npm_deps:
                        name = str(dep.get("name") or "").strip()
                        version = str(dep.get("version") or "").strip()
                        if not name or not version:
                            continue
                        section_name = (
                            "devDependencies" if dep.get(target_field) == "dev" else "dependencies"
                        )
                        section = package_payload.get(section_name)
                        if not isinstance(section, dict):
                            section = {}
                            package_payload[section_name] = section
                        existing = section.get(name)
                        if existing == version:
                            continue
                        section[name] = version
                        changed = True
                    if changed:
                        package_json_path.write_text(
                            json.dumps(package_payload, indent=2) + "\n", encoding="utf-8"
                        )
                        print_success(f"✅ Updated {package_json_path}")
                        _sync_npm_lockfile(project_root)

    for dep in dependencies:
        dep.pop(target_field, None)

    # Check internal modules
    for dep in dependencies:
        if dep.get("source") != "local":
            continue

        raw_name = dep.get("name")
        if not isinstance(raw_name, str):
            continue

        name = raw_name
        if name not in installed_modules:
            print_warning(
                f"⚠️ Internal module {name} not installed. Run `python -m cli.commands.add.module {name} --profile {profile} --project {project}` first."
            )
        else:
            print_info(f"⏭ Internal module {name} already installed")


# def install_module_dependencies(config: Dict, profile: str, project: str, final: bool):
#     """
#     Inject external dependencies into requirements.txt or pyproject.toml and check internal modules in registry.json.
#     """
#     dependencies = config.get("depends_on", {}).get(profile, [])
#     project_root = find_project_root(project)

#     # Path to registry.json in boilerplate root
#     registry_path = project_root / "registry.json"

#     # Load registry
#     try:
#         registry = (
#             json.loads(registry_path.read_text())
#             if registry_path.exists()
#             else {"installed_modules": []}
#         )
#         installed_modules = registry.get("installed_modules", [])
#     except Exception as e:
#         print_warning(f"⚠️ Failed to read registry: {e}")
#         installed_modules = []

#     # Collect external dependencies
#     external_deps = [dep for dep in dependencies if dep.get("source") == "external"]

#     # Inject external dependencies into requirements.txt
#     requirements_file = project_root / "requirements.txt"
#     if external_deps:
#         snippet_content = "\n".join(
#             f"{dep['name']}{dep['version']}" for dep in external_deps
#         )
#         try:
#             new_content = filter_and_update_poetry_dependencies_snippet(
#                 requirements_file, snippet_content
#             )
#             if new_content != (
#                 requirements_file.read_text(encoding="utf-8")
#                 if requirements_file.exists()
#                 else ""
#             ):
#                 requirements_file.write_text(new_content, encoding="utf-8")
#                 print_success(f"✅ Updated {requirements_file}")
#         except Exception as e:
#             print_warning(f"⚠️ Failed to update {requirements_file}: {e}")

#     # Inject external dependencies into pyproject.toml
#     pyproject_file = project_root / "pyproject.toml"
#     if external_deps:
#         snippet_content = "\n".join(
#             f"{dep['name']} = \"{dep['version']}\"" for dep in external_deps
#         )
#         try:
#             new_content = filter_and_update_poetry_dependencies_snippet(
#                 pyproject_file, snippet_content
#             )
#             if new_content != (
#                 pyproject_file.read_text(encoding="utf-8")
#                 if pyproject_file.exists()
#                 else ""
#             ):
#                 pyproject_file.write_text(new_content, encoding="utf-8")
#                 print_success(f"✅ Updated {pyproject_file}")
#         except Exception as e:
#             print_warning(f"⚠️ Failed to update {pyproject_file}: {e}")

#     # Check internal modules
#     for dep in dependencies:
#         name = dep.get("name")
#         source = dep.get("source")
#         if source == "local":
#             if name not in installed_modules:
#                 print_warning(
#                     f"⚠️ Internal module {name} not installed. Run `python -m cli.commands.add.module {name} --profile {profile} --project {project}` first."
#                 )
#             else:
#                 print_info(f"⏭ Internal module {name} already installed")


def _parse_poetry_dependencies_section(
    py_text: str,
) -> Optional[Tuple[str, List[Tuple[str, str]], List[Tuple[str, str]]]]:
    """Extract raw section text and lists of (name,spec) for base and injected blocks.

    Returns None if section or anchor not found.
    """
    anchor = "# <<<inject:module-dependencies>>>"
    start_match = re.search(r"^\[tool\.poetry\.dependencies\]", py_text, re.MULTILINE)
    if not start_match:
        return None
    start_pos = start_match.start()
    next_section_match = re.search(r"^\[.+\]", py_text[start_pos + 1 :], re.MULTILINE)
    end_pos = next_section_match.start() + start_pos + 1 if next_section_match else len(py_text)
    section = py_text[start_pos:end_pos]
    if anchor not in section:
        return None
    before_part, after_part = section.split(anchor, 1)
    base_lines = before_part.splitlines()[1:]  # skip the section header line
    injected_lines = after_part.splitlines()

    def parse_simple_spec(line: str) -> Optional[Tuple[str, str]]:
        pkg, raw_val = parse_poetry_dependency_line(line)
        if not pkg or not raw_val:
            return None
        if pkg == "python":
            return None  # skip python itself
        # dict style: { version = "..", extras=["standard"] }
        if raw_val.startswith("{"):
            # naive parse for version= and extras=
            version_match = re.search(r'version\s*=\s*"([^"]+)"', raw_val)
            if not version_match:
                return None
            version_spec = version_match.group(1)
            extras_match = re.search(r"extras\s*=\s*\[([^\]]+)\]", raw_val)
            if extras_match:
                extras = [
                    e.strip().strip("\"'") for e in extras_match.group(1).split(",") if e.strip()
                ]
                if extras:
                    pkg = f"{pkg}[{','.join(extras)}]"
            return pkg, version_spec
        # quoted string
        m = re.match(r'^"([^"]+)"$', raw_val)
        if m:
            return pkg, m.group(1)
        # unquoted token fallback
        return pkg, raw_val

    base: List[Tuple[str, str]] = []
    for line in base_lines:
        parsed = parse_simple_spec(line)
        if parsed:
            base.append(parsed)
    injected: List[Tuple[str, str]] = []
    for line in injected_lines:
        parsed = parse_simple_spec(line)
        if parsed:
            injected.append(parsed)
    return section, base, injected


def _caret_to_range(spec: str) -> str:
    """Convert Poetry caret spec to explicit range for requirements, else return original.
    Examples:
      ^2.9.0 -> >=2.9.0,<3.0
      ^0.30.0 -> >=0.30.0,<0.31.0
      ^0.0.3 -> >=0.0.3,<0.0.4
    """
    if not spec.startswith("^"):
        return spec
    ver = spec[1:]
    parts = ver.split(".")
    parts += ["0"] * (3 - len(parts))
    major, minor, patch = parts[:3]
    try:
        M = int(major)
        m = int(minor)
        p = int(patch)
    except ValueError:
        return spec  # fallback
    if M > 0:
        return f">={M}.{m}.{p},<{M+1}.0"
    if m > 0:
        return f">={M}.{m}.{p},<{M}.{m+1}.0"
    return f">={M}.{m}.{p},<{M}.{m}.{p+1}"


def _format_requirements_lines(
    base: List[Tuple[str, str]], injected: List[Tuple[str, str]]
) -> Tuple[str, str]:
    """Return (base_block, injected_block) aligned."""
    all_names = [n for n, _ in base] + [n for n, _ in injected]
    if not all_names:
        return "", ""
    max_name = max(len(n) for n in all_names)

    def fmt(entries: List[Tuple[str, str]]) -> str:
        lines = []
        for name, spec in entries:
            spec_adj = _caret_to_range(spec)
            padding = " " * (max_name - len(name) + 1)
            lines.append(f"{name}{padding}{spec_adj}")
        return "\n".join(lines)

    return fmt(base), fmt(injected)


def _sync_requirements_full_from_pyproject(requirements_file: Path, pyproject_file: Path) -> None:
    """Rebuild requirements.txt (base + injected) from pyproject's dependencies section.

    Keeps any leading comment header present in existing requirements file.
    Idempotent and canonical: pyproject is the single source of truth.
    """
    if not pyproject_file.exists():
        return
    py_text = pyproject_file.read_text(encoding="utf-8")
    parsed = _parse_poetry_dependencies_section(py_text)
    if not parsed:
        return
    _raw_section, base, injected = parsed
    # Build blocks
    base_block, injected_block = _format_requirements_lines(base, injected)
    anchor = "# <<<inject:module-dependencies>>>"
    # Preserve leading header comments from existing requirements
    header_lines: List[str] = []
    if requirements_file.exists():
        existing = requirements_file.read_text(encoding="utf-8")
        for line in existing.splitlines():
            if line.strip().startswith("#") or line.strip() == "":
                header_lines.append(line)
            else:
                break
    if not header_lines:
        header_lines = [
            "# Auto-synced from pyproject.toml [tool.poetry.dependencies]",  # provenance
            "# Do not edit dependency versions here directly; edit pyproject.toml instead.",
            "",
        ]
    # Compose new content
    content = "\n".join(header_lines).rstrip("\n") + "\n\n"
    content += base_block.rstrip("\n") + "\n" + anchor + "\n"
    if injected_block:
        content += injected_block.rstrip("\n") + "\n"
    else:
        # ensure newline after anchor
        content += ""
    # Write if changed
    prev = requirements_file.read_text(encoding="utf-8") if requirements_file.exists() else ""
    if content != prev:
        requirements_file.parent.mkdir(parents=True, exist_ok=True)
        requirements_file.write_text(content, encoding="utf-8")
        print_success(f"🔄 Fully synced {requirements_file} from pyproject")


def _extract_requirement_names(block: str) -> List[str]:
    names: List[str] = []
    dep_pattern = re.compile(r"^([A-Za-z0-9_.\-]+(?:\[[^\]]+\])?)[ \t]*[<>=!].+$")
    for line in block.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = dep_pattern.match(s)
        if m:
            names.append(m.group(1))
    return names


def _align_requirements_base_block(before_block: str, injected_names: Iterable[str]) -> str:
    """Align version spec column in base requirements block (before anchor).

    Only adjusts lines that look like dependency specs; leaves comments/blank lines untouched.
    Accounts for injected names to keep one consistent column width.
    """
    lines = before_block.splitlines()
    dep_pattern = re.compile(r"^([A-Za-z0-9_.\-]+(?:\[[^\]]+\])?)([<>=!].+)$")
    entries = []  # (index, name, spec)
    for idx, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = dep_pattern.match(s)
        if m:
            entries.append((idx, m.group(1), m.group(2)))
    if not entries:
        return before_block.rstrip("\n")
    max_len = max(len(name) for _, name, _ in entries)
    for name in injected_names:
        max_len = max(max_len, len(name))
    for idx, name, spec in entries:
        padding = " " * (max_len - len(name) + 1)
        lines[idx] = f"{name}{padding}{spec}"
    return "\n".join(lines)
