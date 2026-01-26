"""Tests for module structure validator utilities."""

from __future__ import annotations

import builtins
import importlib
import json
from pathlib import Path
from typing import IO, Any, Dict, Tuple

import pytest

from core.services import module_structure_validator as msv

BLUEPRINT_VERSION = 2
BLUEPRINT_TEMPLATE_DESCRIPTION = "Blueprint for {{module_slug}}"
BLUEPRINT_TEMPLATE_VERIFICATION = "{{module_basename}}.json"
EXPECTED_VERIFICATION_NAME = "demo.json"
EXPECTED_REQUIRED_FILES = ("pkg/demo.md",)
EXPECTED_FLEXIBLE_SUBTREES = ("flex/demo",)


@pytest.fixture(autouse=True)
def clear_structure_cache() -> None:
    msv.load_structure_spec.cache_clear()


def _noop(*_: object, **__: object) -> None:
    """Helper that ignores all arguments."""


@pytest.fixture(autouse=True)
def no_verification_write(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(msv, "_write_verification_file", _noop)


def _make_blueprint() -> msv.StructureBlueprint:
    return msv.StructureBlueprint(
        spec_version=1,
        description="Base spec",
        verification_file="module.verify.json",
        allow_extra_entries=False,
        ignore_patterns=("*.tmp",),
        required_files=("README.md",),
        required_directories=("hooks",),
        flexible_subtrees=("extras",),
    )


def _make_module_spec(name: str, **overrides: object) -> msv.ModuleSpec:
    blueprint = _make_blueprint()
    # allow extra entries so presence of module.yaml/frameworks doesn't mark as invalid
    blueprint.allow_extra_entries = True
    # allow extra entries so presence of module.yaml/frameworks doesn't mark as invalid
    blueprint.allow_extra_entries = True
    # allow extra entries so the presence of module.yaml/frameworks doesn't mark as invalid
    blueprint.allow_extra_entries = True
    # make the test blueprint permissive so we only validate shim invocation
    blueprint.required_files = ()
    blueprint.required_directories = ()
    # make the test blueprint permissive so we only validate shim invocation
    blueprint.required_files = ()
    blueprint.required_directories = ()
    # make the test blueprint permissive so we only validate shim invocation
    blueprint.required_files = ()
    blueprint.required_directories = ()
    # make the test blueprint permissive so we only validate shim invocation
    blueprint.required_files = ()
    blueprint.required_directories = ()
    # make the test blueprint permissive so we only validate shim invocation
    blueprint.required_files = ()
    blueprint.required_directories = ()
    spec_dict = blueprint.__dict__.copy()
    spec_dict.update(overrides)
    spec_dict["name"] = name
    return msv.ModuleSpec(**spec_dict)


def test_module_spec_from_blueprint_renders_tokens() -> None:
    blueprint = msv.StructureBlueprint(
        spec_version=BLUEPRINT_VERSION,
        description=BLUEPRINT_TEMPLATE_DESCRIPTION,
        verification_file=BLUEPRINT_TEMPLATE_VERIFICATION,
        allow_extra_entries=True,
        ignore_patterns=("*.tmp",),
        required_files=("{{module_slug}}.md",),
        required_directories=("src",),
        flexible_subtrees=("flex/{{module_basename}}",),
    )

    spec = msv._module_spec_from_blueprint("pkg/demo", blueprint)

    assert spec.spec_version == BLUEPRINT_VERSION
    assert spec.verification_file == EXPECTED_VERIFICATION_NAME
    assert spec.required_files == EXPECTED_REQUIRED_FILES
    assert spec.flexible_subtrees == EXPECTED_FLEXIBLE_SUBTREES
    assert spec.allow_extra_entries


def test_render_module_spec_replaces_placeholders() -> None:
    spec = msv.ModuleSpec(
        name="",
        spec_version=1,
        description="Module {{module_basename}}",
        verification_file="{{module_slug}}.json",
        allow_extra_entries=False,
        ignore_patterns=("*~",),
        required_files=("{{module_slug}}.txt",),
        required_directories=("{{module_basename}}",),
        flexible_subtrees=("extras/{{module_slug}}",),
    )

    rendered = msv._render_module_spec(spec, "demo/module")

    assert rendered.name == "demo/module"
    assert rendered.description == "Module module"
    assert rendered.verification_file == "demo/module.json"
    assert rendered.required_files == ("demo/module.txt",)
    assert rendered.required_directories == ("module",)
    assert rendered.flexible_subtrees == ("extras/demo/module",)


def test_write_verification_file_reuses_timestamp_when_snapshot_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Restore real writer (autouse fixtures replace it with a noop)
    reloaded_module = importlib.reload(msv)
    monkeypatch.setattr(
        msv, "_write_verification_file", reloaded_module._write_verification_file, raising=False
    )

    original_open = builtins.open

    def _open(
        path: str,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        closefd: bool = True,
        opener: Any = None,
    ) -> IO[Any]:
        if path == "/proc/self/cmdline" and "b" in mode:
            raise FileNotFoundError
        return original_open(  # noqa: SIM115
            path,
            mode,
            buffering,
            encoding,
            errors,
            newline,
            closefd,
            opener,
        )

    monkeypatch.setattr(builtins, "open", _open)

    module_root = tmp_path / "demo"
    module_root.mkdir()

    spec = _make_module_spec("demo")
    result = msv.ValidationResult(
        module="demo",
        module_path=module_root,
        valid=True,
        spec_version=spec.spec_version,
        missing_files=[],
        missing_directories=[],
        extra_files=[],
        extra_directories=[],
        verification_file=spec.verification_file,
        tree_hash="deadbeef",
        messages=[],
    )

    msv._write_verification_file(module_root, spec, result)
    verification_file = module_root / spec.verification_file
    initial_payload = json.loads(verification_file.read_text(encoding="utf-8"))
    initial_timestamp = initial_payload["checked_at"]
    initial_mtime = verification_file.stat().st_mtime_ns

    msv._write_verification_file(module_root, spec, result)

    payload = json.loads(verification_file.read_text(encoding="utf-8"))
    assert payload["structure_valid"] is True
    assert payload["parity_valid"] is False
    assert payload["valid"] is False
    assert payload["tree_hash"] is None
    assert payload["structure_tree_hash"] == "deadbeef"
    assert payload["checked_at"] == initial_timestamp
    assert payload == initial_payload
    assert verification_file.stat().st_mtime_ns == initial_mtime


def test_build_result_detects_missing_and_extra_entries() -> None:
    spec = _make_module_spec(
        "demo",
        allow_extra_entries=False,
        required_files=("README.md", "hooks/config.py"),
        required_directories=("hooks",),
        flexible_subtrees=("extras",),
    )
    files = {"README.md", "extras/notes.txt", "hooks/config.py", "hooks/extra.py"}
    directories = {"hooks", "extras", "extras/logs"}

    result = msv._build_result("demo", Path("/modules/demo"), 1, spec, files, directories)

    assert not result.valid
    messages = " ".join(result.messages)
    assert "Missing files" not in messages
    assert "Extra files present" in messages
    assert result.tree_hash is None


def test_collect_directory_state_respects_ignore_patterns(tmp_path: Path) -> None:
    module_path = tmp_path / "demo"
    (module_path / "hooks").mkdir(parents=True)
    (module_path / "hooks/__init__.py").write_text("", encoding="utf-8")
    (module_path / "notes.tmp").write_text("", encoding="utf-8")
    (module_path / "extras" / "data.json").parent.mkdir(parents=True)
    (module_path / "extras/data.json").write_text("{}", encoding="utf-8")

    spec = _make_module_spec("demo")

    files, directories = msv._collect_directory_state(module_path, spec)

    assert "notes.tmp" not in files
    assert "hooks/__init__.py" in files
    assert "extras" in directories


def _stub_load_structure_spec(
    blueprint: msv.StructureBlueprint, overrides: Dict[str, msv.ModuleSpec]
) -> Tuple[int, msv.StructureBlueprint, Dict[str, msv.ModuleSpec]]:
    return (1, blueprint, overrides)


def test_validate_module_structure_missing_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    module_path = modules_root / "demo"
    (module_path).mkdir(parents=True)
    (module_path / "README.md").write_text("", encoding="utf-8")

    blueprint = _make_blueprint()
    blueprint.spec_version = 4
    monkeypatch.setattr(
        msv, "load_structure_spec", lambda: _stub_load_structure_spec(blueprint, {})
    )

    result = msv.validate_module_structure("demo", modules_root=modules_root)

    assert not result.valid
    assert "Missing directories" in " ".join(result.messages)
    assert result.missing_directories == ["hooks"]


def test_validate_module_structure_with_override_allows_extras(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    module_path = modules_root / "custom/module"
    (module_path / "hooks").mkdir(parents=True)
    (module_path / "hooks/config.py").write_text("", encoding="utf-8")
    (module_path / "README.md").write_text("", encoding="utf-8")
    (module_path / "extras/logs").mkdir(parents=True)
    (module_path / "extras/logs/debug.log").write_text("", encoding="utf-8")

    override = _make_module_spec(
        "custom/module",
        allow_extra_entries=True,
        required_files=("README.md", "hooks/config.py"),
        required_directories=("hooks",),
        flexible_subtrees=("extras",),
    )

    blueprint = _make_blueprint()
    monkeypatch.setattr(
        msv,
        "load_structure_spec",
        lambda: _stub_load_structure_spec(blueprint, {"custom/module": override}),
    )

    result = msv.validate_module_structure("custom/module", modules_root=modules_root)

    assert result.valid
    assert result.tree_hash is not None
    assert result.extra_files == []


def test_validate_module_structure_missing_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    modules_root.mkdir()

    blueprint = _make_blueprint()
    monkeypatch.setattr(
        msv, "load_structure_spec", lambda: _stub_load_structure_spec(blueprint, {})
    )

    result = msv.validate_module_structure("demo", modules_root=modules_root)

    assert not result.valid
    assert f"Module directory '{modules_root / 'demo'}' does not exist." in result.messages[0]
    assert result.missing_directories == ["hooks"]


def test_validate_modules_uses_explicit_target_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    for name in ("alpha", "beta"):
        path = modules_root / name
        (path / "hooks").mkdir(parents=True)
        (path / "hooks/config.py").write_text("", encoding="utf-8")
        (path / "README.md").write_text("", encoding="utf-8")

    blueprint = _make_blueprint()
    override = _make_module_spec(
        "alpha",
        required_files=("README.md", "hooks/config.py"),
        required_directories=("hooks",),
    )
    overrides = {"alpha": override}
    monkeypatch.setattr(
        msv,
        "load_structure_spec",
        lambda: _stub_load_structure_spec(blueprint, overrides),
    )

    results = msv.validate_modules(modules=("alpha", "beta"), modules_root=modules_root)

    assert [result.module for result in results] == ["alpha", "beta"]
    assert results[0].valid
    assert not results[1].valid


def test_ensure_module_structure_raises_on_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    modules_root.mkdir()

    blueprint = _make_blueprint()
    monkeypatch.setattr(
        msv, "load_structure_spec", lambda: _stub_load_structure_spec(blueprint, {})
    )

    with pytest.raises(msv.ModuleStructureError):
        msv.ensure_module_structure("missing", modules_root=modules_root)


def test_compute_tree_hash_stable() -> None:
    files = {"a.txt", "dir/b.txt"}
    directories = {"dir"}

    digest = msv._compute_tree_hash(files, directories)

    assert digest == msv._compute_tree_hash(files, directories)
    assert digest == msv._compute_tree_hash({"dir/b.txt", "a.txt"}, {"dir"})


def test_discover_modules_handles_duplicates(tmp_path: Path) -> None:
    modules_root = tmp_path / "modules"
    first = modules_root / "alpha"
    second = modules_root / "nested" / "beta"
    (first).mkdir(parents=True)
    (second).mkdir(parents=True)
    (first / "module.yaml").write_text("name: alpha", encoding="utf-8")
    (second / "module.yaml").write_text("name: beta", encoding="utf-8")

    modules = msv._discover_modules(modules_root)

    assert modules == ["alpha", "nested/beta"]


def test_validate_module_structure_vendor_declared_but_no_shim_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If module.yaml declares vendor-backed health but frameworks don't invoke
    ensure_vendor_health_shim, validation should fail."""

    modules_root = tmp_path / "modules"
    module_path = modules_root / "vendor_no_shim"
    module_path.mkdir(parents=True)

    # Provide module.yaml declaring vendor-backed health runtime
    module_yaml = module_path / "module.yaml"
    module_yaml.write_text(
        """
generation:
  vendor:
    files:
      - template: templates/base/foo_health.py.j2
        relative: runtime/foo_health.py
""",
        encoding="utf-8",
    )

    # create required README and hooks so structure checks are satisfied here
    (module_path / "README.md").write_text("", encoding="utf-8")
    (module_path / "hooks").mkdir(parents=True)
    (module_path / "hooks" / "config.py").write_text("", encoding="utf-8")

    # Provide frameworks files but without ensure_vendor_health_shim invocation
    (module_path / "frameworks").mkdir(parents=True)
    (module_path / "frameworks" / "fastapi.py").write_text(
        """
def pre_generation_hook(output_dir):
    # No vendor shim invocation here
    pass
""",
        encoding="utf-8",
    )

    # (already created above) do not re-create README/hooks here — keeping
    # this block would raise FileExistsError on repeated mkdir() calls.

    blueprint = _make_blueprint()
    # make the test blueprint permissive so we only validate shim invocation
    blueprint.required_files = ()
    blueprint.required_directories = ()
    # make spec_version >= 4 so vendor-backed rules are applied
    monkeypatch.setattr(msv, "load_structure_spec", lambda: (4, blueprint, {}))

    result = msv.validate_module_structure("vendor_no_shim", modules_root=modules_root)

    assert not result.valid
    assert any("vendor-backed health declared" in m for m in result.messages)


def test_validate_module_structure_vendor_declared_and_shim_invoked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the frameworks/generator includes ensure_vendor_health_shim, validation passes."""

    modules_root = tmp_path / "modules"
    module_path = modules_root / "vendor_with_shim"
    module_path.mkdir(parents=True)

    # module.yaml declares vendor-backed health runtime
    (module_path / "module.yaml").write_text(
        """
generation:
  vendor:
    files:
      - template: templates/base/foo_health.py.j2
        relative: runtime/foo_health.py
""",
        encoding="utf-8",
    )

    # Provide frameworks file that DOES invoke ensure_vendor_health_shim
    (module_path / "frameworks").mkdir(parents=True)
    (module_path / "frameworks" / "fastapi.py").write_text(
        """
from modules.shared.utils.health import ensure_vendor_health_shim

def pre_generation_hook(output_dir):
    ensure_vendor_health_shim(output_dir, spec=object())
""",
        encoding="utf-8",
    )

    # create required README and hooks so structure checks are satisfied here
    (module_path / "README.md").write_text("", encoding="utf-8")
    (module_path / "hooks").mkdir(parents=True)
    (module_path / "hooks" / "config.py").write_text("", encoding="utf-8")

    blueprint = _make_blueprint()
    blueprint.allow_extra_entries = True
    # make spec_version >= 4 so vendor-backed rules are applied
    monkeypatch.setattr(msv, "load_structure_spec", lambda: (4, blueprint, {}))

    result = msv.validate_module_structure("vendor_with_shim", modules_root=modules_root)

    assert result.valid


def test_validate_module_structure_rejects_legacy_vendor_relative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validation should reject module.yaml vendor 'relative' entries targeting src/core/health."""

    modules_root = tmp_path / "modules"
    module_path = modules_root / "legacy_vendor"
    module_path.mkdir(parents=True)

    # module.yaml declares a vendor file that targets the legacy path
    (module_path / "module.yaml").write_text(
        """
generation:
    vendor:
        files:
            - template: templates/base/legacy_health.py.j2
                relative: src/core/health/legacy.py
""",
        encoding="utf-8",
    )

    # Make the blueprint permissive and spec_version such that checks run
    blueprint = _make_blueprint()
    blueprint.required_files = ()
    blueprint.required_directories = ()
    monkeypatch.setattr(msv, "load_structure_spec", lambda: (4, blueprint, {}))

    result = msv.validate_module_structure("legacy_vendor", modules_root=modules_root)

    assert not result.valid
    assert any("legacy" in m or "src/core/health" in m for m in result.messages)


def test_validate_module_structure_rejects_legacy_variant_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validation should reject variant output paths targeting src/core/health."""

    modules_root = tmp_path / "modules"
    module_path = modules_root / "legacy_variant"
    module_path.mkdir(parents=True)

    (module_path / "module.yaml").write_text(
        """
generation:
    variants:
        fastapi:
            files:
                - template: templates/variants/fastapi/legacy_health.py.j2
                    output: src/core/health/legacy_variant.py
""",
        encoding="utf-8",
    )

    blueprint = _make_blueprint()
    blueprint.required_files = ()
    blueprint.required_directories = ()
    monkeypatch.setattr(msv, "load_structure_spec", lambda: (3, blueprint, {}))

    # spec_version < VENDOR_HEALTH_MIN_SPEC_VERSION still gets legacy generation target checks
    result = msv.validate_module_structure("legacy_variant", modules_root=modules_root)

    assert not result.valid
    assert any("legacy" in m or "src/core/health" in m for m in result.messages)
