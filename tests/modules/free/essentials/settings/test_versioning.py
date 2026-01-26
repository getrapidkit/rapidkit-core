import json
import shutil
from pathlib import Path

import pytest
import yaml
from packaging.version import Version

from core.services.module_versioning import DEFAULT_PENDING_CHANGELOG_FILENAME
from modules.free.essentials.settings import generate
from modules.shared import versioning


def _clone_module(src_root: Path, destination: Path) -> Path:
    def _ignore(directory: str, contents: list[str]) -> set[str]:
        baseline = {"__pycache__", ".pytest_cache", ".git"}
        ignored = {name for name in contents if name in baseline}
        if Path(directory) == src_root:
            ignored.add(".module_state.json")
        return ignored

    shutil.copytree(src_root, destination, ignore=_ignore)
    return destination


def test_auto_version_bumps_when_inputs_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module_root = _clone_module(generate.MODULE_ROOT, tmp_path / "module")

    monkeypatch.setattr(generate, "MODULE_ROOT", module_root, raising=False)

    config = generate.load_module_config()
    config, changed = versioning.ensure_version_consistency(config, module_root=module_root)
    assert not changed


def test_pending_changelog_file_enriches_changelog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module_root = _clone_module(generate.MODULE_ROOT, tmp_path / "module")

    monkeypatch.setattr(generate, "MODULE_ROOT", module_root, raising=False)

    config = generate.load_module_config()
    config, changed = versioning.ensure_version_consistency(config, module_root=module_root)
    assert not changed

    pending_payload = {
        "description": "Refreshed template outputs",
        "changes": [
            {
                "type": "feature",
                "description": "Ship centralized versioning",
                "scope": "python",
            },
        ],
        "metadata": {
            "commit": "deadbeef",
        },
        "breaking_changes": [],
        "deprecations": [],
    }

    pending_path = module_root / DEFAULT_PENDING_CHANGELOG_FILENAME
    pending_path.write_text(
        yaml.safe_dump(pending_payload, sort_keys=False),
        encoding="utf-8",
    )

    template_path = module_root / "templates" / "vendor" / "nestjs" / "configuration.js.j2"
    template_path.write_text(
        template_path.read_text(encoding="utf-8") + "\n// pending changelog mutation\n",
        encoding="utf-8",
    )

    config, changed = versioning.ensure_version_consistency(config, module_root=module_root)
    assert changed

    module_config = yaml.safe_load((module_root / "module.yaml").read_text(encoding="utf-8"))
    head_entry = module_config["changelog"][0]
    assert head_entry["version"] == str(config["version"])
    assert head_entry.get("notes") == "See docs/changelog.md"

    docs_changelog = (module_root / "docs" / "changelog.md").read_text(encoding="utf-8")
    assert f"## {config['version']}" in docs_changelog
    assert "scope=python" in docs_changelog
    assert "commit=deadbeef" in docs_changelog

    assert not pending_path.exists()

    baseline_version = Version(str(config["version"]))

    template_path = module_root / "templates" / "variants" / "fastapi" / "settings.py.j2"
    template_path.write_text(template_path.read_text() + "\n# smoke mutation\n", encoding="utf-8")

    config, changed = versioning.ensure_version_consistency(config, module_root=module_root)
    assert changed

    bumped_version = Version(str(config["version"]))
    assert bumped_version > baseline_version

    state_payload = json.loads((module_root / ".module_state.json").read_text(encoding="utf-8"))
    assert state_payload["version"] == str(bumped_version)

    module_config = yaml.safe_load((module_root / "module.yaml").read_text(encoding="utf-8"))
    assert module_config["changelog"][0]["version"] == str(bumped_version)

    config, changed = versioning.ensure_version_consistency(config, module_root=module_root)
    assert not changed
