from __future__ import annotations

import json
from pathlib import Path

from core.services.snippet_injector import inject_snippet_enterprise, rollback_snippet_injection


def test_rollback_removes_injected_block_and_sets_pending(tmp_path: Path):
    target = tmp_path / "app.py"
    target.write_text("# header\n# <<<inject:settings-fields>>>\n", encoding="utf-8")

    snippet_template = tmp_path / "t.j2"
    snippet_template.write_text("DB_URL: str = 'postgresql://x'\n", encoding="utf-8")

    res = inject_snippet_enterprise(
        destination_path=target,
        template_path=snippet_template,
        anchor="# <<<inject:settings-fields>>>",
        variables={},
        snippet_metadata={
            "id": "x",
            "version": "1.0.0",
            "priority": 1,
            "template": "t.j2",
            "module_slug": "free/database/db_postgres",
            "context": {},
            "conflict_resolution": "merge",
        },
        project_root=tmp_path,
        lenient=False,
    )
    assert res["injected"] is True

    out = target.read_text(encoding="utf-8")
    assert "<<<inject:settings-fields:x:start>>>" in out
    assert "postgresql://x" in out
    assert "<<<inject:settings-fields:x:end>>>" in out

    reg = json.loads((tmp_path / ".rapidkit" / "snippet_registry.json").read_text(encoding="utf-8"))
    assert reg["snippets"]["x::app.py"]["status"] == "applied"

    rb = rollback_snippet_injection(tmp_path, key="x::app.py", dry_run=False)
    assert rb["status"] == "rolled_back"

    out2 = target.read_text(encoding="utf-8")
    assert "<<<inject:settings-fields:x:start>>>" not in out2
    assert "postgresql://x" not in out2
    assert "<<<inject:settings-fields:x:end>>>" not in out2
    # Anchor remains
    assert "<<<inject:settings-fields>>>" in out2

    reg2 = json.loads(
        (tmp_path / ".rapidkit" / "snippet_registry.json").read_text(encoding="utf-8")
    )
    assert reg2["snippets"]["x::app.py"]["status"] == "pending"
    assert reg2["snippets"]["x::app.py"].get("rolled_back_at")

    audit_path = tmp_path / ".rapidkit" / "audit" / "snippet_injections.jsonl"
    assert audit_path.exists()
    events = [
        json.loads(ln) for ln in audit_path.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    assert any(e.get("event") == "snippet_rollback" and e.get("key") == "x::app.py" for e in events)


def test_rollback_dry_run_does_not_write(tmp_path: Path):
    target = tmp_path / "app.py"
    target.write_text(
        "# <<<inject:settings-fields>>>\n# <<<inject:settings-fields:x:start>>>\nX=1\n# <<<inject:settings-fields:x:end>>>\n",
        encoding="utf-8",
    )

    (tmp_path / "snippet_registry.json").write_text(
        json.dumps({"snippets": {"x::app.py": {"status": "applied", "file": "app.py"}}}, indent=2),
        encoding="utf-8",
    )

    before = target.read_text(encoding="utf-8")
    before_reg = (tmp_path / "snippet_registry.json").read_text(encoding="utf-8")

    rb = rollback_snippet_injection(tmp_path, key="x::app.py", dry_run=True)
    assert rb["status"] == "rolled_back"

    assert target.read_text(encoding="utf-8") == before
    assert (tmp_path / "snippet_registry.json").read_text(encoding="utf-8") == before_reg
    assert not (tmp_path / ".rapidkit").exists()
