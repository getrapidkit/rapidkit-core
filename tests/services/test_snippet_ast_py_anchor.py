from __future__ import annotations

from pathlib import Path

import pytest

from core.services import snippet_injector


def test_ast_py_inserts_after_anchor_line_without_black(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Force libcst parse checks to pass and force libcst anchor finder to a known line.
    monkeypatch.setattr(snippet_injector, "_try_parse_python_with_libcst", lambda _: None)
    monkeypatch.setattr(snippet_injector, "_find_python_anchor_line_with_libcst", lambda *_: 1)

    called = {"count": 0}

    def _fake_format_with_black(text: str):
        called["count"] += 1
        return (text, None)

    monkeypatch.setattr(snippet_injector, "_format_with_black", _fake_format_with_black)

    target = tmp_path / "app.py"
    # anchor is on line index 1 (0-based): second line
    target.write_text("# a\n# <<<inject:settings-fields>>>\n# b\n", encoding="utf-8")

    tpl = tmp_path / "t.j2"
    tpl.write_text("X = 1\n", encoding="utf-8")

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
            "patch_mode": "ast_py",
        },
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is True
    assert called["count"] == 0

    out = target.read_text(encoding="utf-8")
    # inserted block should appear between anchor line and "# b"
    assert "<<<inject:settings-fields:x:start>>>" in out
    assert "X = 1" in out
    assert "<<<inject:settings-fields:x:end>>>" in out
