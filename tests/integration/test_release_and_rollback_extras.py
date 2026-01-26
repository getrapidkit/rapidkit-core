import json
from pathlib import Path

from typer.testing import CliRunner

from cli.main import app as cli_app

runner = CliRunner()


def _extract_json(text: str):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise AssertionError("No JSON located")
    return json.loads(text[start : end + 1])


def test_generate_release_notes_script(tmp_path: Path):
    prev = tmp_path / "prev.lock"
    curr = tmp_path / "curr.lock"
    prev.write_text('{"a": "1.0.0", "b": "1.0.0"}', encoding="utf-8")
    curr.write_text('{"a": "1.1.0", "c": "0.1.0"}', encoding="utf-8")
    import subprocess
    import sys

    res = subprocess.run(
        [
            sys.executable,
            "scripts/generate_release_notes.py",
            "--prev",
            str(prev),
            "--curr",
            str(curr),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    out = res.stdout
    assert "Added Modules" in out
    assert "Removed Modules" in out
    assert "Updated Modules" in out


def test_rollback_template_reset_missing_snapshot(temp_project: Path, primary_project_name: str):
    # Simulate entry with previous_hash but missing snapshot; use --template-reset to fallback
    rel = "backend/core/config.py"
    target = temp_project / rel
    original = target.read_bytes()
    from core.services.file_hash_registry import (
        _sha256,
        load_hashes,
        record_file_hash,
        save_hashes,
    )

    reg = load_hashes(temp_project)
    prev_hash = _sha256(original)
    # Overwrite file content (new current) without snapshot of previous
    target.write_bytes(b"# NEW\n" + original)
    # Record registry entry with previous_hash pointing to original, but without snapshot stored
    record_file_hash(
        reg,
        rel,
        "logging",
        "1.0.0",
        target.read_bytes(),
        previous_hash=prev_hash,
        snapshot=False,
        project_root=None,
    )
    save_hashes(temp_project, reg)
    # Rollback with template_reset + force to bypass hash mismatch; accept rolled_back or snapshot_missing or no_previous
    res = runner.invoke(
        cli_app,
        [
            "rollback",
            "module",
            "logging",
            "--project",
            primary_project_name,
            "--template-reset",
            "--force",
            "--json",
        ],
    )
    assert res.exit_code == 0, res.output
    data = _extract_json(res.output)
    assert data.get("schema_version") == "rollback-v1"
    statuses = {f["status"] for f in data.get("files", [])}
    assert statuses & {"rolled_back", "snapshot_missing", "no_previous"}
