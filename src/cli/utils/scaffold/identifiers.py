"""Identifier derivation helpers for module scaffolding."""

from __future__ import annotations

import copy
import datetime as dt
import json
import re
from pathlib import Path
from string import Template
from typing import Any, Dict, Iterable, List, Mapping

from .blueprints import get_blueprint
from .constants import REPOSITORY_INTEGRATION_SUFFIX, REPOSITORY_TEST_SUFFIXES

_SIMPLE_SCALAR_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


def _format_scalar(value: object) -> str:
    result: str
    if isinstance(value, bool):
        result = "true" if value else "false"
    elif value is None:
        result = "null"
    elif isinstance(value, (int, float)):
        result = str(value)
    elif isinstance(value, str):
        if value == "":
            result = '""'
        elif _SIMPLE_SCALAR_RE.fullmatch(value):
            result = value
        else:
            result = json.dumps(value)
    else:
        result = json.dumps(value)
    return result


def _unique_sequence(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen and item:
            seen.add(item)
            ordered.append(item)
    return ordered


def _render_block_list(items: Iterable[str], *, indent: str) -> str:
    values = _unique_sequence(items)
    if not values:
        return f"{indent}[]"
    return "\n".join(f"{indent}- {item}" for item in values)


def _render_block_mapping(data: Mapping[str, object], *, indent: str) -> str:
    lines: List[str] = []
    for key, value in data.items():
        if isinstance(value, Mapping):
            lines.append(f"{indent}{key}:")
            nested = _render_block_mapping(value, indent=f"{indent}  ")
            if nested:
                lines.append(nested)
            continue
        if isinstance(value, (list, tuple)):
            if not value:
                lines.append(f"{indent}{key}: []")
                continue
            lines.append(f"{indent}{key}:")
            for item in value:
                if isinstance(item, Mapping):
                    lines.append(f"{indent}  -")
                    nested = _render_block_mapping(item, indent=f"{indent}    ")
                    if nested:
                        lines.append(nested)
                else:
                    lines.append(f"{indent}  - {_format_scalar(item)}")
            continue
        lines.append(f"{indent}{key}: {_format_scalar(value)}")
    return "\n".join(lines)


def _render_fixture_block(items: Iterable[str]) -> str:
    values = _unique_sequence(items)
    if not values:
        return " []"
    rendered = "\n".join(f"    - {item}" for item in values)
    return f"\n{rendered}"


def derive_identifiers(
    tier: str,
    category: str,
    module_name: str,
    description: str | None,
    blueprint: str | None = None,
) -> Dict[str, str]:
    """Compute contextual identifiers used across scaffold templates."""

    today_date = dt.date.today().isoformat()

    tier_slug = _validate_slug(tier, label="tier")
    category_slug = _validate_category(category)
    module_slug = _validate_slug(module_name, label="module name")

    title = _to_title(module_slug)
    class_name = _to_class_name(module_slug)
    kebab = module_slug.replace("_", "-")
    category_path = [part for part in category_slug.split("/") if part]
    category_display = "/".join(category_path) if category_path else "core"

    python_output_rel = Path("src", *category_path, f"{module_slug}.py").as_posix()
    python_types_rel = Path("src", *category_path, f"{module_slug}_types.py").as_posix()
    python_health_rel = Path("src", "health", *category_path, f"{module_slug}.py").as_posix()
    python_router_rel = Path("src", "routers", *category_path, f"{module_slug}.py").as_posix()

    nest_base_dir = Path("src", module_slug.replace("_", "-"))
    nest_service_rel = (nest_base_dir / f"{module_slug}.service.ts").as_posix()
    nest_controller_rel = (nest_base_dir / f"{module_slug}.controller.ts").as_posix()
    nest_module_rel = (nest_base_dir / f"{module_slug}.module.ts").as_posix()
    nest_health_rel = (nest_base_dir / f"{module_slug}.health.ts").as_posix()
    nest_validation_rel = (nest_base_dir / f"{module_slug}.validation.ts").as_posix()
    nest_index_rel = (nest_base_dir / "index.ts").as_posix()
    nest_configuration_rel = (nest_base_dir / "configuration.ts").as_posix()

    vendor_relative = Path("src", *category_path, f"{module_slug}.py").as_posix()
    vendor_types_relative = Path("src", *category_path, f"{module_slug}_types.py").as_posix()
    vendor_health_relative = Path("src", "health", *category_path, f"{module_slug}.py").as_posix()
    module_package_import = ".".join(["modules", tier_slug, *category_path, module_slug])
    module_import_path = module_package_import
    module_frameworks_import = module_package_import + ".frameworks"
    module_generator_class = f"{class_name}ModuleGenerator"
    module_entry_point_group = f"rapidkit.{module_slug}.plugins"

    selected_blueprint = get_blueprint(blueprint)
    baseline_blueprint = get_blueprint("baseline")

    description_text = (
        (description or "").strip()
        or selected_blueprint.summary
        or baseline_blueprint.summary
        or f"Bootstrap implementation for {title}."
    )
    display_name = selected_blueprint.display_name or title

    compatibility_map: Dict[str, object] = dict(baseline_blueprint.compatibility)
    if selected_blueprint.key != baseline_blueprint.key:
        compatibility_map.update(selected_blueprint.compatibility)

    testing_config: Dict[str, object] = dict(baseline_blueprint.testing)
    if selected_blueprint.key != baseline_blueprint.key:
        testing_config.update(selected_blueprint.testing)

    fixtures_raw: Any = testing_config.pop("fixtures", [])
    if isinstance(fixtures_raw, (list, tuple)):
        fixtures = [str(item) for item in fixtures_raw if str(item)]
    elif fixtures_raw:
        fixtures = [str(fixtures_raw)]
    else:
        fixtures = []

    tags_seed = [*selected_blueprint.tags, *category_path]
    if not tags_seed:
        tags_seed = [category_display]
    tags_block = _render_block_list(tags_seed, indent="  ")

    capability_source = list(selected_blueprint.capabilities) or list(
        baseline_blueprint.capabilities
    )
    capability_names = [cap.name for cap in capability_source]
    capabilities_block = _render_block_list(capability_names, indent="  ")
    if capability_source:
        capabilities_md = "\n".join(
            f"- **{cap.name.replace('_', ' ').title()}** – {cap.description}"
            for cap in capability_source
        )
    else:
        capabilities_md = "- TODO: Document module capabilities."

    highlights = list(selected_blueprint.highlights) or [description_text]
    highlights_md = "\n".join(f"- {item}" for item in highlights)

    module_summary = description_text
    module_description_literal = _format_scalar(module_summary)
    module_display_name_literal = _format_scalar(display_name)
    compatibility_block = _render_block_mapping(compatibility_map, indent="  ")
    testing_coverage_min = _format_scalar(testing_config.get("coverage_min", 0))
    testing_integration_tests = _format_scalar(testing_config.get("integration_tests", True))
    testing_e2e_tests = _format_scalar(testing_config.get("e2e_tests", False))
    testing_fixtures_block = _render_fixture_block(fixtures)

    render_context = {
        "module_title": title,
        "module_name": module_slug,
        "module_display_name": display_name,
        "module_summary": module_summary,
        "module_description": module_summary,
        "tier": tier_slug,
    }

    baseline_base_config = copy.deepcopy(baseline_blueprint.base_config)
    base_config_map = (
        copy.deepcopy(selected_blueprint.base_config)
        if selected_blueprint.base_config
        else baseline_base_config
    )
    if not base_config_map:
        base_config_block = "\nprofiles: {}\nvariables: {}\ndev_dependencies: []"
    else:
        rendered_base_config = _render_block_mapping(base_config_map, indent="")
        rendered_base_config = Template(rendered_base_config).safe_substitute(render_context)
        if rendered_base_config:
            base_config_block = f"\n{rendered_base_config}"
        else:
            base_config_block = "\nprofiles: {}"

    baseline_snippet_config = copy.deepcopy(baseline_blueprint.snippet_config)
    snippet_config_map = (
        copy.deepcopy(selected_blueprint.snippet_config)
        if selected_blueprint.snippet_config
        else baseline_snippet_config or {"snippets": []}
    )
    rendered_snippet_config = _render_block_mapping(snippet_config_map, indent="")
    rendered_snippet_config = Template(rendered_snippet_config).safe_substitute(render_context)
    snippet_config_block = rendered_snippet_config or "snippets: []"

    doc_relative_dir = Path("docs")
    doc_overview_rel_module = (doc_relative_dir / "overview.md").as_posix()
    doc_usage_rel_module = (doc_relative_dir / "usage.md").as_posix()
    doc_advanced_rel_module = (doc_relative_dir / "advanced.md").as_posix()
    doc_changelog_rel_module = (doc_relative_dir / "changelog.md").as_posix()
    doc_migration_rel_module = (doc_relative_dir / "migration.md").as_posix()
    doc_troubleshooting_rel_module = (doc_relative_dir / "troubleshooting.md").as_posix()
    doc_api_reference_rel_module = (doc_relative_dir / "api-reference.md").as_posix()
    doc_overview_path = doc_overview_rel_module
    doc_usage_path = doc_usage_rel_module
    doc_advanced_path = doc_advanced_rel_module
    doc_changelog_path = doc_changelog_rel_module
    doc_migration_path = doc_migration_rel_module
    doc_troubleshooting_path = doc_troubleshooting_rel_module
    doc_api_reference_path = doc_api_reference_rel_module
    module_slug_test_path = (
        f"{tier_slug}_{'_'.join(category_path) + '_' if category_path else ''}{module_slug}"
    )
    tests_repo_relative = Path(
        "tests", "modules", tier_slug, *category_path, module_slug
    ).as_posix()
    tests_integration_relative = Path(
        "tests", "modules", tier_slug, "integration", *category_path, module_slug
    ).as_posix()
    unit_test_files = [
        (Path(tests_repo_relative) / f"test_{module_slug}_{suffix}.py").as_posix()
        for suffix in REPOSITORY_TEST_SUFFIXES
    ]
    unit_tests_yaml_lines = "\n".join(f"    - {name}" for name in unit_test_files)
    unit_tests_yaml = f"  unit_tests:\n{unit_tests_yaml_lines}"
    integration_test_path = Path(
        tests_integration_relative, f"test_{module_slug}_{REPOSITORY_INTEGRATION_SUFFIX}.py"
    ).as_posix()

    return {
        "tier": tier_slug,
        "category": category_display or "core",
        "category_path": "/".join(category_path) if category_path else "core",
        "category_import": ".".join(category_path) if category_path else "core",
        "module_name": module_slug,
        "module_name_upper": module_slug.upper(),
        "module_title": title,
        "module_title_lower": title.lower(),
        "module_display_name": display_name,
        "module_display_name_literal": module_display_name_literal,
        "module_class": class_name,
        "module_kebab": kebab,
        "module_slug": f"{tier_slug}/{'/'.join(category_path) if category_path else 'core'}/{module_slug}",
        "module_slug_test_path": module_slug_test_path,
        "module_description": module_summary,
        "module_summary": module_summary,
        "module_description_literal": module_description_literal,
        "module_highlights_md": highlights_md,
        "module_capabilities_md": capabilities_md,
        "module_tags_block": tags_block,
        "module_capabilities_block": capabilities_block,
        "module_compatibility_block": compatibility_block,
        "testing_coverage_min": testing_coverage_min,
        "testing_integration_tests": testing_integration_tests,
        "testing_e2e_tests": testing_e2e_tests,
        "module_testing_fixtures_block": testing_fixtures_block,
        "module_blueprint_key": selected_blueprint.key,
        "module_base_config_block": base_config_block.rstrip(),
        "module_snippet_config_block": snippet_config_block.rstrip(),
        "python_output_rel": python_output_rel,
        "python_types_rel": python_types_rel,
        "python_health_rel": python_health_rel,
        "python_router_rel": python_router_rel,
        "nest_service_rel": nest_service_rel,
        "nest_output_rel": nest_service_rel,
        "nest_controller_rel": nest_controller_rel,
        "nest_module_rel": nest_module_rel,
        "nest_health_rel": nest_health_rel,
        "nest_validation_rel": nest_validation_rel,
        "nest_index_rel": nest_index_rel,
        "nest_configuration_rel": nest_configuration_rel,
        "vendor_relative": vendor_relative,
        "vendor_types_relative": vendor_types_relative,
        "vendor_health_relative": vendor_health_relative,
        "module_import_path": module_import_path,
        "module_package_import": module_package_import,
        "module_frameworks_import": module_frameworks_import,
        "module_generator_class": module_generator_class,
        "module_entry_point_group": module_entry_point_group,
        "doc_relative_dir": doc_relative_dir.as_posix(),
        "doc_overview_path": doc_overview_path,
        "doc_usage_path": doc_usage_path,
        "doc_advanced_path": doc_advanced_path,
        "doc_changelog_path": doc_changelog_path,
        "doc_migration_path": doc_migration_path,
        "doc_troubleshooting_path": doc_troubleshooting_path,
        "doc_api_reference_path": doc_api_reference_path,
        "doc_overview_rel_module": doc_overview_rel_module,
        "doc_usage_rel_module": doc_usage_rel_module,
        "doc_advanced_rel_module": doc_advanced_rel_module,
        "doc_changelog_rel_module": doc_changelog_rel_module,
        "doc_migration_rel_module": doc_migration_rel_module,
        "doc_troubleshooting_rel_module": doc_troubleshooting_rel_module,
        "doc_api_reference_rel_module": doc_api_reference_rel_module,
        "today_date": today_date,
        "tests_repo_relative": tests_repo_relative,
        "tests_integration_relative": tests_integration_relative,
        "module_integration_test": integration_test_path,
        "module_unit_tests_yaml": unit_tests_yaml,
    }


def _validate_slug(value: str, *, label: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if not re.fullmatch(r"[a-z0-9_]+", normalized):
        raise ValueError(f"Invalid {label} '{value}'. Use lower-case letters, digits, '-' or '_'.")
    return normalized


def _validate_category(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").strip("/")
    if not normalized:
        return "core"
    if not re.fullmatch(r"[a-z0-9_/]+", normalized):
        raise ValueError(
            "Invalid category. Use lower-case letters, digits, '-', '_' and '/' for nesting."
        )
    return normalized


def _to_title(value: str) -> str:
    parts = [part for part in re.split(r"[-_]+", value) if part]
    return " ".join(word.capitalize() for word in parts) or value.capitalize()


def _to_class_name(value: str) -> str:
    parts = [part for part in re.split(r"[-_]+", value) if part]
    return "".join(word.capitalize() for word in parts) or value.title().replace(" ", "")


__all__ = ["derive_identifiers"]
