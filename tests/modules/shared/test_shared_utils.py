import json
from pathlib import Path

import pytest

from modules.shared.utils import (
    extract_module_dependencies,
    format_module_identifier,
    get_module_metadata,
    get_module_version,
    is_valid_module_name,
    load_module_manifest,
    merge_configurations,
    normalize_module_name,
    resolve_module_path,
    validate_module_structure,
)

_NEW_VALUE = 2


def write_manifest(module_root: Path, payload: dict) -> None:
    manifest_path = module_root / "module.json"
    module_root.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_module_manifest_returns_empty_when_missing(tmp_path: Path) -> None:
    module_root = tmp_path / "missing"
    module_root.mkdir()

    assert load_module_manifest(module_root) == {}


def test_load_module_manifest_reads_json(tmp_path: Path) -> None:
    module_root = tmp_path / "present"
    data = {"name": "Example", "version": "1.2.3"}
    write_manifest(module_root, data)

    assert load_module_manifest(module_root) == data


def test_load_module_manifest_raises_on_invalid_json(tmp_path: Path) -> None:
    module_root = tmp_path / "invalid"
    manifest = module_root / "module.json"
    module_root.mkdir()
    manifest.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError):
        load_module_manifest(module_root)


def test_get_module_version_defaults(tmp_path: Path) -> None:
    module_root = tmp_path / "defaults"
    module_root.mkdir()

    assert get_module_version(module_root) == "0.1.0"


def test_get_module_version_from_manifest(tmp_path: Path) -> None:
    module_root = tmp_path / "versioned"
    write_manifest(module_root, {"version": "9.9.9"})

    assert get_module_version(module_root) == "9.9.9"


def test_normalize_and_resolve_module_name(tmp_path: Path) -> None:
    base = tmp_path
    name = "My Module-Name"

    normalized = normalize_module_name(name)
    assert normalized == "my_module_name"
    assert resolve_module_path(base, name) == base / normalized


def test_merge_configurations_deep_merge() -> None:
    base = {"nested": {"keep": True, "overwrite": False}, "scalar": 1}
    overrides = {"nested": {"overwrite": True}, "new": _NEW_VALUE}

    merged = merge_configurations(base, overrides)

    assert merged["nested"] == {"keep": True, "overwrite": True}
    assert merged["scalar"] == 1
    assert merged["new"] == _NEW_VALUE


def test_validate_module_structure_requires_manifest(tmp_path: Path) -> None:
    module_root = tmp_path / "structure"
    module_root.mkdir()

    assert not validate_module_structure(module_root)
    write_manifest(module_root, {"name": "structure"})
    assert validate_module_structure(module_root)


@pytest.mark.parametrize(
    "module_name, version, expected",
    [
        ("Example", None, "example"),
        ("Example", "1.0.0", "example@1.0.0"),
    ],
)
def test_format_module_identifier(module_name: str, version: str | None, expected: str) -> None:
    assert format_module_identifier(module_name, version) == expected


def test_extract_module_dependencies(tmp_path: Path) -> None:
    module_root = tmp_path / "deps"
    write_manifest(module_root, {"dependencies": {"alpha": "1.0"}})

    assert extract_module_dependencies(module_root) == {"alpha": "1.0"}


@pytest.mark.parametrize(
    "candidate, expected",
    [
        ("module_name", True),
        ("Module-1", True),
        ("", False),
        ("1module", False),
        ("invalid@name", False),
    ],
)
def test_is_valid_module_name(candidate: str, expected: bool) -> None:
    assert is_valid_module_name(candidate) is expected


def test_get_module_metadata_includes_defaults(tmp_path: Path) -> None:
    module_root = tmp_path / "meta"
    payload = {"name": "Meta", "version": "2.0", "dependencies": {"core": "*"}}
    write_manifest(module_root, payload)

    metadata = get_module_metadata(module_root)

    assert metadata["name"] == "Meta"
    assert metadata["version"] == "2.0"
    assert metadata["dependencies"] == {"core": "*"}
    assert metadata["tags"] == []
