from __future__ import annotations

from pathlib import Path

import pytest

from core.services import snippet_injector


def test_no_touch_mode_skips_black_formatting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "app.py"
    # Deliberately awkward formatting outside the injection block.
    target.write_text(
        "def  f():\n    return   1\n# <<<inject:settings-fields>>>\n", encoding="utf-8"
    )

    tpl = tmp_path / "t.j2"
    tpl.write_text("X=1\n", encoding="utf-8")

    called = {"count": 0}

    def _fake_format_with_black(text: str):
        called["count"] += 1
        return ("BLACK_WOULD_HAVE_CHANGED_THIS\n", None)

    monkeypatch.setattr(snippet_injector, "_format_with_black", _fake_format_with_black)

    res = snippet_injector.inject_snippet_enterprise(
        destination_path=target,
        template_path=tpl,
        anchor="# <<<inject:settings-fields>>>",
        variables={},
        snippet_metadata={
            "id": "x",
            "version": "1.0.0",
            "priority": 1,
            "template": "t.j2",
            "module_slug": "free/database/db_postgres",
            "context": {},
            "conflict_resolution": "override",
            "patch_mode": "no_touch",
        },
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is True
    assert called["count"] == 0

    out = target.read_text(encoding="utf-8")
    assert "BLACK_WOULD_HAVE_CHANGED_THIS" not in out
    assert "<<<inject:settings-fields:x:start>>>" in out
