#!/usr/bin/env python3
"""Validate RapidKit module scaffolds against the canonical STRUCTURE.yaml spec."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

module_structure_cli = importlib.import_module("cli.utils.module_structure_cli")
DEFAULT_MODULES_ROOT = module_structure_cli.DEFAULT_MODULES_ROOT
collect_validation_results = module_structure_cli.collect_validation_results
ensure_module_validation = module_structure_cli.ensure_module_validation
ensure_structure_spec_ready = module_structure_cli.ensure_structure_spec_ready
validation_result_to_dict = module_structure_cli.validation_result_to_dict
validation_results_to_dict = module_structure_cli.validation_results_to_dict
validation_summary_lines = module_structure_cli.validation_summary_lines


_FASTAPI_ANCHOR_RE = re.compile(r"^\s*fastapi:\s*&fastapi_variant\s*(?:#.*)?$")
_NESTJS_ANCHOR_RE = re.compile(r"^\s*nestjs:\s*&nestjs_variant\s*(?:#.*)?$")
_FASTAPI_STANDARD_RE = re.compile(r"^\s*fastapi\.standard:\s*\*fastapi_variant\s*(?:#.*)?$")
_FASTAPI_DDD_RE = re.compile(r"^\s*fastapi\.ddd:\s*\*fastapi_variant\s*(?:#.*)?$")
_NESTJS_STANDARD_RE = re.compile(r"^\s*nestjs\.standard:\s*\*nestjs_variant\s*(?:#.*)?$")
_ANON_ANCHOR_RE = re.compile(r"(?:&id\d+|\*id\d+)")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _is_safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    if path.is_absolute():
        return False
    # Disallow path traversal and weird drive-like prefixes.
    parts = path.parts
    if any(part in {"..", ""} for part in parts):
        return False
    return True


def _module_yaml_schema_errors(module_slug: str, modules_root: Path) -> List[str]:
    errors: List[str] = []
    module_dir = (modules_root / module_slug).resolve()
    module_yaml = module_dir / "module.yaml"

    if not module_yaml.exists():
        return [f"module.yaml not found at {module_yaml}"]

    raw = ""
    try:
        raw = module_yaml.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"unable to read module.yaml: {exc}"]

    try:
        data: object = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:  # type: ignore[attr-defined]
        return [f"YAML parse error (safe_load): {exc}"]

    if not isinstance(data, dict):
        return ["module.yaml must be a mapping"]

    # Basic slug consistency checks.
    TIER_INDEX = 0
    CATEGORY_INDEX = 1
    MIN_PARTS_FOR_TIER = 1
    MIN_PARTS_FOR_CATEGORY = 2

    parts = [p for p in module_slug.split("/") if p]
    tier_dir = parts[TIER_INDEX] if len(parts) >= MIN_PARTS_FOR_TIER else ""
    category_dir = parts[CATEGORY_INDEX] if len(parts) >= MIN_PARTS_FOR_CATEGORY else ""

    name_val = data.get("name")
    if not isinstance(name_val, str) or not name_val:
        errors.append("missing or invalid required key: name")

    category_val = data.get("category")
    if not isinstance(category_val, str) or not category_val:
        errors.append("missing or invalid required key: category")
    elif category_dir and category_val != category_dir:
        errors.append(f"category must equal module slug category '{category_dir}'")

    access_val = data.get("access")
    if not isinstance(access_val, str) or not access_val:
        errors.append("missing or invalid required key: access")
    elif tier_dir in {"free", "paid"} and access_val != tier_dir:
        errors.append(f"access must equal '{tier_dir}' for module slug '{module_slug}'")

    tier_val = data.get("tier")
    if not isinstance(tier_val, str) or not tier_val:
        errors.append("missing or invalid required key: tier")
    elif tier_dir == "free" and tier_val != "free":
        errors.append("tier must be 'free' for free/* modules")
    elif tier_dir == "paid" and tier_val not in {"paid", "pro", "enterprise"}:
        errors.append("tier must be one of 'paid'|'pro'|'enterprise' for paid/* modules")

    # Description: allow either top-level description or metadata.description.
    description_val = data.get("description")
    metadata_val = data.get("metadata")
    metadata_description = None
    if isinstance(metadata_val, dict):
        metadata_description = metadata_val.get("description")
    if not (
        isinstance(description_val, str)
        and description_val.strip()
        or isinstance(metadata_description, str)
        and metadata_description.strip()
    ):
        errors.append("missing description (provide 'description' or 'metadata.description')")

    version_val = data.get("version")
    if not isinstance(version_val, str) or not version_val:
        errors.append("missing or invalid required key: version")

    status_val = data.get("status")
    if not isinstance(status_val, str) or not status_val:
        errors.append("missing or invalid required key: status")

    tags_val = data.get("tags")
    if not isinstance(tags_val, list) or not all(isinstance(t, str) for t in tags_val):
        errors.append("tags must be a list of strings")

    gfc = data.get("generated_from_config")
    if not isinstance(gfc, bool):
        errors.append("generated_from_config must be a boolean")

    profile_inherits_val = data.get("profile_inherits")
    if not isinstance(profile_inherits_val, dict):
        errors.append("profile_inherits must be a mapping")

    config_sources_val = data.get("config_sources")
    if not isinstance(config_sources_val, list) or not all(
        isinstance(item, str) for item in config_sources_val
    ):
        errors.append("config_sources must be a list of strings")

    # Core generation schema.
    generation_val = data.get("generation")
    if not isinstance(generation_val, dict):
        errors.append("generation must be a mapping")
    else:
        vendor_val = generation_val.get("vendor")
        if not isinstance(vendor_val, dict):
            errors.append("generation.vendor must be a mapping")
        else:
            if not isinstance(vendor_val.get("root"), str) or not vendor_val.get("root"):
                errors.append("generation.vendor.root must be a non-empty string")
            vendor_files = vendor_val.get("files")
            if not isinstance(vendor_files, list) or not vendor_files:
                errors.append("generation.vendor.files must be a non-empty list")
            else:
                for idx, entry in enumerate(vendor_files, start=1):
                    if not isinstance(entry, dict):
                        errors.append(f"generation.vendor.files[{idx}] must be a mapping")
                        continue
                    if not isinstance(entry.get("template"), str) or not entry.get("template"):
                        errors.append(f"generation.vendor.files[{idx}].template must be a string")
                    if not _is_safe_relative_path(entry.get("relative")):
                        errors.append(
                            f"generation.vendor.files[{idx}].relative must be a safe relative path"
                        )

        variants_val = generation_val.get("variants")
        if not isinstance(variants_val, dict):
            errors.append("generation.variants must be a mapping")
        else:
            # Base variants should be present; alias compliance is handled separately.
            for base_variant in ("fastapi", "nestjs"):
                variant_mapping = variants_val.get(base_variant)
                if not isinstance(variant_mapping, dict):
                    errors.append(f"generation.variants.{base_variant} must be a mapping")
                    continue
                if not isinstance(variant_mapping.get("root"), str) or not variant_mapping.get(
                    "root"
                ):
                    errors.append(
                        f"generation.variants.{base_variant}.root must be a non-empty string"
                    )
                ctx = variant_mapping.get("context")
                if not isinstance(ctx, dict):
                    errors.append(f"generation.variants.{base_variant}.context must be a mapping")
                files = variant_mapping.get("files")
                if not isinstance(files, list) or not files:
                    errors.append(
                        f"generation.variants.{base_variant}.files must be a non-empty list"
                    )
                    continue
                for idx, entry in enumerate(files, start=1):
                    if not isinstance(entry, dict):
                        errors.append(
                            f"generation.variants.{base_variant}.files[{idx}] must be a mapping"
                        )
                        continue
                    if not isinstance(entry.get("template"), str) or not entry.get("template"):
                        errors.append(
                            f"generation.variants.{base_variant}.files[{idx}].template must be a string"
                        )
                    if not _is_safe_relative_path(entry.get("output")):
                        errors.append(
                            f"generation.variants.{base_variant}.files[{idx}].output must be a safe relative path"
                        )

    # Snippets schema: matches celery-style manifests (generation.snippets).
    snippets_val = generation_val.get("snippets") if isinstance(generation_val, dict) else None
    if not isinstance(snippets_val, dict):
        errors.append("generation.snippets must be a mapping")
    else:
        if not isinstance(snippets_val.get("enabled"), bool):
            errors.append("generation.snippets.enabled must be a boolean")
        if not isinstance(snippets_val.get("config"), str) or not snippets_val.get("config"):
            errors.append("generation.snippets.config must be a non-empty string")
        default_val = snippets_val.get("default")
        if not isinstance(default_val, list) or not all(
            isinstance(item, str) for item in default_val
        ):
            errors.append("generation.snippets.default must be a list of strings")

    # Compatibility / testing / docs are required top-level sections.
    for key in ("compatibility", "testing", "documentation", "support", "changelog"):
        if key not in data:
            errors.append(f"missing required key: {key}")

    # Validation/rollback/performance/capabilities are required by the scaffold template.
    if "validation" not in data:
        errors.append("missing required key: validation")
    else:
        validation_val = data.get("validation")
        if not isinstance(validation_val, dict):
            errors.append("validation must be a mapping")
        else:
            for phase in ("pre_install", "post_install"):
                lst = validation_val.get(phase)
                if not isinstance(lst, list) or not all(isinstance(item, str) for item in lst):
                    errors.append(f"validation.{phase} must be a list of strings")

    if "rollback" not in data:
        errors.append("missing required key: rollback")
    else:
        rollback_val = data.get("rollback")
        if not isinstance(rollback_val, dict):
            errors.append("rollback must be a mapping")
        else:
            if not isinstance(rollback_val.get("strategy"), str) or not rollback_val.get(
                "strategy"
            ):
                errors.append("rollback.strategy must be a non-empty string")
            if not _is_safe_relative_path(rollback_val.get("backup_path")):
                errors.append("rollback.backup_path must be a safe relative path")
            if not isinstance(rollback_val.get("max_backups"), int):
                errors.append("rollback.max_backups must be an integer")

    if "performance" not in data:
        errors.append("missing required key: performance")
    else:
        performance_val = data.get("performance")
        if not isinstance(performance_val, dict):
            errors.append("performance must be a mapping")
        else:
            if not isinstance(performance_val.get("lazy_loading"), bool):
                errors.append("performance.lazy_loading must be a boolean")
            caching_val = performance_val.get("caching")
            if not isinstance(caching_val, dict):
                errors.append("performance.caching must be a mapping")
            else:
                if not isinstance(caching_val.get("templates"), bool):
                    errors.append("performance.caching.templates must be a boolean")
                if not isinstance(caching_val.get("ttl"), int):
                    errors.append("performance.caching.ttl must be an integer")

    if "capabilities" not in data:
        errors.append("missing required key: capabilities")
    else:
        capabilities_val = data.get("capabilities")
        if not isinstance(capabilities_val, list) or not all(
            isinstance(item, str) for item in capabilities_val
        ):
            errors.append("capabilities must be a list of strings")

    # Signature envelope + file_hashes.
    if "signature" not in data:
        errors.append("missing required key: signature")
    else:
        sig = data.get("signature")
        if sig is not None and not isinstance(sig, dict):
            errors.append("signature must be a mapping or null")
        if isinstance(sig, dict):
            for k in ("signature", "signer_id", "signature_version"):
                if k not in sig:
                    errors.append(f"signature.{k} is required when signature is a mapping")
                else:
                    v = sig.get(k)
                    if v is not None and not isinstance(v, str):
                        errors.append(f"signature.{k} must be a string or null")

    # These top-level keys exist across the repo and are treated as part of the canonical schema.
    for k in ("signer_id", "signature_version"):
        if k not in data:
            errors.append(f"missing required key: {k}")
        else:
            v = data.get(k)
            if v is not None and not isinstance(v, str):
                errors.append(f"{k} must be a string or null")

    file_hashes_val = data.get("file_hashes")
    if not isinstance(file_hashes_val, dict) or not file_hashes_val:
        errors.append("file_hashes must be a non-empty mapping")
    else:
        for path_key, hash_val in file_hashes_val.items():
            if not isinstance(path_key, str) or not path_key:
                errors.append("file_hashes keys must be non-empty strings")
                break
            if not isinstance(hash_val, str) or not _SHA256_RE.match(hash_val):
                errors.append(f"file_hashes.{path_key} must be of form 'sha256:<64hex>'")
                break

    return errors


def _resolve_paths(raw_paths: Sequence[str]) -> List[Path]:
    resolved: List[Path] = []
    for raw in raw_paths:
        path = Path(raw)
        path = (REPO_ROOT / path).resolve() if not path.is_absolute() else path.resolve()
        resolved.append(path)
    return resolved


def _discover_module_slugs(modules_root: Path) -> List[str]:
    slugs: List[str] = []
    for module_yaml in modules_root.glob("**/module.yaml"):
        module_dir = module_yaml.parent.resolve()
        try:
            slug = module_dir.relative_to(modules_root.resolve()).as_posix()
        except ValueError:
            continue
        slugs.append(slug)
    return sorted(set(slugs))


def _mapping_get(node: yaml.nodes.Node | None, key: str) -> yaml.nodes.Node | None:
    if node is None or not isinstance(node, yaml.nodes.MappingNode):
        return None
    for k_node, v_node in node.value:
        if isinstance(k_node, yaml.nodes.ScalarNode) and k_node.value == key:
            return v_node
    return None


def _module_yaml_standard_errors(module_slug: str, modules_root: Path) -> List[str]:
    errors: List[str] = []
    base = (modules_root / module_slug).resolve()
    module_yaml = base / "module.yaml"
    raw = ""
    if not module_yaml.exists():
        errors.append(f"module.yaml not found at {module_yaml}")
    else:
        try:
            raw = module_yaml.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"unable to read module.yaml: {exc}")

    # 1) Parse and locate generation.variants block for strict text checks.
    root_node: yaml.nodes.Node | None = None
    if not errors:
        try:
            root_node = yaml.compose(raw)
        except yaml.YAMLError as exc:  # type: ignore[attr-defined]
            errors.append(f"YAML parse error: {exc}")

    if not errors and root_node is None:
        errors.append("module.yaml is empty or invalid YAML")

    variants_node: yaml.nodes.Node | None = None
    if not errors:
        generation_node = _mapping_get(root_node, "generation")
        variants_node = _mapping_get(generation_node, "variants")

        if variants_node is None:
            errors.append("missing required key: generation.variants")
        elif not isinstance(variants_node, yaml.nodes.MappingNode):
            errors.append("generation.variants must be a mapping")

    variants_lines: List[str] = []
    start = 0
    if not errors and isinstance(variants_node, yaml.nodes.MappingNode):
        lines = raw.splitlines()
        start = getattr(variants_node.start_mark, "line", 0)
        end_mark_line = getattr(variants_node.end_mark, "line", start)
        end = min(len(lines), max(start + 1, end_mark_line + 1))
        variants_lines = lines[start:end]

    if not errors:
        # Guard: anonymous anchors are not allowed in variants section.
        for idx, line in enumerate(variants_lines, start=1):
            if _ANON_ANCHOR_RE.search(line):
                errors.append(
                    f"generation.variants uses anonymous YAML anchor on line {start + idx}: {line.strip()}"
                )
                break

    def _find_all(regex: re.Pattern[str]) -> List[int]:
        hits: List[int] = []
        for i, line in enumerate(variants_lines):
            if regex.match(line):
                hits.append(i)
        return hits

    fastapi_anchor = _find_all(_FASTAPI_ANCHOR_RE)
    nestjs_anchor = _find_all(_NESTJS_ANCHOR_RE)
    fastapi_std = _find_all(_FASTAPI_STANDARD_RE)
    fastapi_ddd = _find_all(_FASTAPI_DDD_RE)
    nestjs_std = _find_all(_NESTJS_STANDARD_RE)

    def _require_exactly_one(label: str, hits: List[int]) -> None:
        if len(hits) == 1:
            return
        if not hits:
            errors.append(f"generation.variants is missing required entry: {label}")
        else:
            errors.append(f"generation.variants has duplicate entries for: {label}")

    _require_exactly_one("fastapi: &fastapi_variant", fastapi_anchor)
    _require_exactly_one("fastapi.standard: *fastapi_variant", fastapi_std)
    _require_exactly_one("fastapi.ddd: *fastapi_variant", fastapi_ddd)
    _require_exactly_one("nestjs: &nestjs_variant", nestjs_anchor)
    _require_exactly_one("nestjs.standard: *nestjs_variant", nestjs_std)

    # Ordering constraints: aliases must come after their anchor definitions.
    if len(fastapi_anchor) == 1:
        anchor_pos = fastapi_anchor[0]
        for label, hits in (("fastapi.standard", fastapi_std), ("fastapi.ddd", fastapi_ddd)):
            if len(hits) == 1 and hits[0] < anchor_pos:
                errors.append(f"{label} alias appears before fastapi anchor (&fastapi_variant)")
    if len(nestjs_anchor) == 1 and len(nestjs_std) == 1:
        if nestjs_std[0] < nestjs_anchor[0]:
            errors.append("nestjs.standard alias appears before nestjs anchor (&nestjs_variant)")

    # 2) Semantic checks: ensure aliases are real YAML aliases (same object), not copied blocks.
    data: object = {}
    if not errors:
        try:
            data = yaml.safe_load(raw) or {}
        except yaml.YAMLError as exc:  # type: ignore[attr-defined]
            errors.append(f"YAML parse error (safe_load): {exc}")

    generation = data.get("generation") if isinstance(data, dict) else None
    if not isinstance(generation, dict):
        errors.append("generation must be a mapping")

    variants_dict: dict[str, object] | None = None
    if isinstance(generation, dict):
        variants_obj = generation.get("variants")
        if isinstance(variants_obj, dict):
            variants_dict = variants_obj
        else:
            errors.append("generation.variants must be a mapping")

    if variants_dict is not None:
        required_keys = {
            "fastapi",
            "fastapi.standard",
            "fastapi.ddd",
            "nestjs",
            "nestjs.standard",
        }
        missing = [k for k in sorted(required_keys) if k not in variants_dict]
        if missing:
            errors.append("generation.variants missing keys: " + ", ".join(missing))
        else:
            if variants_dict.get("fastapi.standard") is not variants_dict.get("fastapi"):
                errors.append("fastapi.standard must be a YAML alias to fastapi (&fastapi_variant)")
            if variants_dict.get("fastapi.ddd") is not variants_dict.get("fastapi"):
                errors.append("fastapi.ddd must be a YAML alias to fastapi (&fastapi_variant)")
            if variants_dict.get("nestjs.standard") is not variants_dict.get("nestjs"):
                errors.append("nestjs.standard must be a YAML alias to nestjs (&nestjs_variant)")

    # profile_inherits should map kit profiles back to base variant names.
    profile_inherits = data.get("profile_inherits") if isinstance(data, dict) else None
    if not isinstance(profile_inherits, dict):
        errors.append("profile_inherits must be a mapping")
    else:
        expected = {
            "fastapi.standard": "fastapi",
            "fastapi.ddd": "fastapi",
            "nestjs.standard": "nestjs",
        }
        for key, value in expected.items():
            if profile_inherits.get(key) != value:
                errors.append(f"profile_inherits.{key} must equal '{value}'")

    return errors


def _build_module_index(modules_root: Path) -> Dict[Path, str]:
    index: Dict[Path, str] = {}
    for module_yaml in modules_root.glob("**/module.yaml"):
        module_dir = module_yaml.parent.resolve()
        try:
            slug = module_dir.relative_to(modules_root.resolve()).as_posix()
        except ValueError:
            continue
        index[module_dir] = slug
    return index


def _modules_from_paths(paths: Iterable[Path], modules_root: Path) -> Optional[Set[str]]:
    modules_root = modules_root.resolve()
    index = _build_module_index(modules_root)
    discovered: Set[str] = set()
    for path in paths:
        normalized = path.resolve()
        slug = None
        for module_dir, module_slug in index.items():
            try:
                normalized.relative_to(module_dir)
                slug = module_slug
                break
            except ValueError:
                continue
        if slug is None:
            return None
        discovered.add(slug)
    return discovered if discovered else None


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "modules",
        nargs="*",
        help="Specific module slugs to validate (e.g. 'free/essentials/settings').",
    )
    parser.add_argument(
        "--modules-root",
        type=Path,
        default=DEFAULT_MODULES_ROOT,
        help="Root directory containing modules (defaults to repository src/modules).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary of the results.",
    )
    parser.add_argument(
        "--strict-module-yaml",
        action="store_true",
        help=(
            "Strictly validate module.yaml generation.variants follows the canonical "
            "celery-style anchors/aliases (fastapi/nestjs + kit profile aliases)."
        ),
    )
    parser.add_argument(
        "--strict-module-yaml-schema",
        action="store_true",
        help=(
            "Strictly validate module.yaml required fields and canonical section shapes "
            "(generation/vendor/snippets/testing/docs/signature/file_hashes, etc.)."
        ),
    )
    parser.add_argument(
        "--only-module-yaml-standard",
        action="store_true",
        help="Only run strict module.yaml standard validation (skip STRUCTURE.yaml checks).",
    )
    parser.add_argument(
        "--only-module-yaml",
        action="store_true",
        help=(
            "Only run strict module.yaml validations (standard/schema) and skip STRUCTURE.yaml checks."
        ),
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failing module instead of reporting all results.",
    )
    parser.add_argument(
        "--ensure",
        metavar="MODULE",
        help="Ensure a module slug exists and raises on failure. Shortcut for --json single module.",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        help="File paths used to infer module validation scope (for tooling integration).",
    )
    args = parser.parse_args(argv)

    only_module_yaml = bool(args.only_module_yaml_standard or args.only_module_yaml)

    if not only_module_yaml:
        try:
            ensure_structure_spec_ready()
        except (FileNotFoundError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    if args.ensure:
        yaml_standard_errors: List[str] = []
        yaml_schema_errors: List[str] = []
        if args.strict_module_yaml:
            yaml_standard_errors = _module_yaml_standard_errors(args.ensure, args.modules_root)
        if args.strict_module_yaml_schema:
            yaml_schema_errors = _module_yaml_schema_errors(args.ensure, args.modules_root)

        if only_module_yaml:
            combined_valid = not yaml_standard_errors and not yaml_schema_errors
            if args.json:
                print(
                    json.dumps(
                        {
                            "module": args.ensure,
                            "valid": combined_valid,
                            "module_yaml_standard": {
                                "valid": not yaml_standard_errors,
                                "messages": yaml_standard_errors,
                            },
                            "module_yaml_schema": {
                                "valid": not yaml_schema_errors,
                                "messages": yaml_schema_errors,
                            },
                        },
                        indent=2,
                    )
                )
            else:
                status = "PASS" if combined_valid else "FAIL"
                print(f"{args.ensure}: {status}")
                for msg in yaml_standard_errors + yaml_schema_errors:
                    print(f"  - {msg}")
            return 0 if combined_valid else 1

        result, error = ensure_module_validation(args.ensure, args.modules_root)
        if args.json:
            payload = validation_result_to_dict(result)
            if args.strict_module_yaml:
                payload["module_yaml_standard"] = {
                    "valid": not yaml_standard_errors,
                    "messages": yaml_standard_errors,
                }
            if args.strict_module_yaml_schema:
                payload["module_yaml_schema"] = {
                    "valid": not yaml_schema_errors,
                    "messages": yaml_schema_errors,
                }
            if args.strict_module_yaml or args.strict_module_yaml_schema:
                payload["valid"] = bool(
                    payload["valid"] and not yaml_standard_errors and not yaml_schema_errors
                )
            print(json.dumps(payload, indent=2))
        else:
            _, lines = validation_summary_lines([result], fail_fast=False)
            for line in lines:
                print(line)
            if args.strict_module_yaml:
                status = "PASS" if not yaml_standard_errors else "FAIL"
                print(f"module.yaml standard: {status}")
                for msg in yaml_standard_errors:
                    print(f"  - {msg}")
            if args.strict_module_yaml_schema:
                status = "PASS" if not yaml_schema_errors else "FAIL"
                print(f"module.yaml schema: {status}")
                for msg in yaml_schema_errors:
                    print(f"  - {msg}")
        if error or yaml_standard_errors or yaml_schema_errors:
            if error:
                print(str(error))
            return 1
        return 0

    target_modules: Optional[Sequence[str]]
    explicit_modules: Set[str] = set(args.modules)

    if args.paths:
        candidate_paths = _resolve_paths(args.paths)
        inferred_modules = _modules_from_paths(candidate_paths, args.modules_root)
        if inferred_modules is None:
            target_modules = None
        else:
            explicit_modules.update(inferred_modules)
            target_modules = tuple(sorted(explicit_modules)) if explicit_modules else None
    else:
        target_modules = tuple(sorted(explicit_modules)) if explicit_modules else None

    yaml_standard_summary: dict[str, dict[str, object]] = {}
    yaml_schema_summary: dict[str, dict[str, object]] = {}
    yaml_exit_code = 0
    if args.strict_module_yaml or args.strict_module_yaml_schema:
        slugs = (
            list(target_modules) if target_modules else _discover_module_slugs(args.modules_root)
        )
        for slug in slugs:
            std_messages: List[str] = []
            schema_messages: List[str] = []
            if args.strict_module_yaml:
                std_messages = _module_yaml_standard_errors(slug, args.modules_root)
                yaml_standard_summary[slug] = {"valid": not std_messages, "messages": std_messages}
            if args.strict_module_yaml_schema:
                schema_messages = _module_yaml_schema_errors(slug, args.modules_root)
                yaml_schema_summary[slug] = {
                    "valid": not schema_messages,
                    "messages": schema_messages,
                }

            if std_messages or schema_messages:
                yaml_exit_code = 1
                if args.fail_fast:
                    break

    if only_module_yaml:
        if args.json:
            print(
                json.dumps(
                    {
                        "modules_root": str(args.modules_root),
                        "valid": yaml_exit_code == 0,
                        "module_yaml_standard": yaml_standard_summary,
                        "module_yaml_schema": yaml_schema_summary,
                    },
                    indent=2,
                )
            )
        else:
            slugs = (
                list(target_modules)
                if target_modules
                else _discover_module_slugs(args.modules_root)
            )
            for slug in slugs:
                std_record = yaml_standard_summary.get(slug, {"valid": True, "messages": []})
                schema_record = yaml_schema_summary.get(slug, {"valid": True, "messages": []})
                valid = bool(std_record.get("valid") and schema_record.get("valid"))
                status = "PASS" if valid else "FAIL"
                print(f"{slug}: {status}")
                for record in (std_record, schema_record):
                    messages_obj_1: object = record.get("messages")
                    messages_list_1: list[str] = (
                        [str(item) for item in messages_obj_1]
                        if isinstance(messages_obj_1, list)
                        else []
                    )
                    for msg in messages_list_1:
                        print(f"  - {msg}")
        return yaml_exit_code

    results = collect_validation_results(target_modules, args.modules_root)
    exit_code, lines = validation_summary_lines(results, args.fail_fast)
    exit_code = max(exit_code, yaml_exit_code)

    if args.json:
        payload = validation_results_to_dict(results, args.modules_root)
        if args.strict_module_yaml:
            payload["module_yaml_standard"] = yaml_standard_summary
        if args.strict_module_yaml_schema:
            payload["module_yaml_schema"] = yaml_schema_summary
        if args.strict_module_yaml or args.strict_module_yaml_schema:
            payload["valid"] = bool(payload.get("valid") and yaml_exit_code == 0)
        print(json.dumps(payload, indent=2))
    else:
        for line in lines:
            print(line)
        if args.strict_module_yaml:
            for slug, record in yaml_standard_summary.items():
                status = "PASS" if record.get("valid") else "FAIL"
                print(f"module.yaml standard ({slug}): {status}")
                messages_obj_2: object = record.get("messages")
                messages_list_2: list[str] = (
                    [str(item) for item in messages_obj_2]
                    if isinstance(messages_obj_2, list)
                    else []
                )
                for msg in messages_list_2:
                    print(f"  - {msg}")
        if args.strict_module_yaml_schema:
            for slug, record in yaml_schema_summary.items():
                status = "PASS" if record.get("valid") else "FAIL"
                print(f"module.yaml schema ({slug}): {status}")
                messages_obj_3: object = record.get("messages")
                messages_list_3: list[str] = (
                    [str(item) for item in messages_obj_3]
                    if isinstance(messages_obj_3, list)
                    else []
                )
                for msg in messages_list_3:
                    print(f"  - {msg}")

    return exit_code


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
