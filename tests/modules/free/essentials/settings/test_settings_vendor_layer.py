import importlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

settings_generate = importlib.import_module("modules.free.essentials.settings.generate")


@pytest.mark.integration
def test_nestjs_settings_installer_writes_vendor_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("typer")
    add_module = importlib.import_module("cli.commands.add.module")

    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "package.json").write_text(
        json.dumps({"dependencies": {"@nestjs/core": "^10.0.0"}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(add_module, "install_module_dependencies", lambda *_a, **_k: None)
    monkeypatch.setattr(
        add_module, "prompt_for_variables", lambda _config: {"project_name": "acme-service"}
    )
    monkeypatch.setattr(add_module, "find_project_root", lambda _project: project_root)
    monkeypatch.setattr(add_module, "ensure_module_structure", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "enforce_module_gating", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "copy_extra_files", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "inject_snippet_enterprise", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "remove_inject_anchors", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "organize_imports", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "process_translations", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "update_registry", lambda *_a, **_k: None)

    hash_registry: dict[str, Any] = {"files": {}}
    monkeypatch.setattr(add_module, "load_hashes", lambda _root: hash_registry)
    monkeypatch.setattr(add_module, "file_was_modified", lambda *_a, **_k: False)
    monkeypatch.setattr(add_module, "record_file_hash", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "save_hashes", lambda *_a, **_k: None)
    monkeypatch.setattr(add_module, "ensure_init_files", lambda *_a, **_k: None)

    original_which = shutil.which
    original_run = subprocess.run

    class _FakeCompletedProcess:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = ""

    def _fake_which(command: str) -> str | None:
        if command in {"node", "npm", "tsc", "npx"}:
            return f"/usr/bin/{command}"
        return original_which(command)

    monkeypatch.setattr(shutil, "which", _fake_which)

    def _fake_run(args: Any, **kwargs: Any) -> Any:
        if isinstance(args, (list, tuple)) and args:
            binary = str(args[0])
            if binary.endswith("node") and len(args) > 1 and args[1] == "--version":
                return _FakeCompletedProcess(stdout="v18.18.0\n", returncode=0)
            if binary.endswith("npm") or binary.endswith("npx") or binary.endswith("tsc"):
                return _FakeCompletedProcess()
        return original_run(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", _fake_run)

    original_store = add_module.store_vendor_file
    store_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def capture_store(*args: Any, **kwargs: Any) -> None:
        store_calls.append((args, kwargs))
        original_store(*args, **kwargs)

    monkeypatch.setattr(add_module, "store_vendor_file", capture_store)

    add_module.add_module(
        "free/essentials/settings",
        profile="nestjs/standard",
        project=str(project_root),
        final=False,
        force=False,
        update=False,
        plan=False,
    )

    config = settings_generate.load_module_config()
    vendor_module = str(config.get("name", "settings"))
    vendor_version = str(config.get("version", "0.0.0"))

    vendor_root = project_root / ".rapidkit" / "vendor" / vendor_module / vendor_version
    assert vendor_root.exists(), "vendor snapshot directory missing"

    vendor_configuration_path = vendor_root / "nestjs" / "configuration.js"
    assert vendor_configuration_path.exists(), "vendor configuration snapshot missing"
    vendor_configuration = vendor_configuration_path.read_text(encoding="utf-8")
    assert "module.exports" in vendor_configuration

    generated_configuration_path = (
        project_root / "src" / "modules" / "free" / "essentials" / "settings" / "configuration.ts"
    )
    assert generated_configuration_path.exists(), "generated configuration missing"
    generated_configuration = generated_configuration_path.read_text(encoding="utf-8")
    assert "registerAs" in generated_configuration

    stored_paths = {Path(args[3]).as_posix() for args, _ in store_calls}
    assert {"nestjs/configuration.js"}.issubset(stored_paths)
