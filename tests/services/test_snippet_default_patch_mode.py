from __future__ import annotations

from pathlib import Path

import pytest

from core.services import snippet_injector


def test_default_patch_mode_python_is_ast_py(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Force ast_py path to be deterministic and not depend on libcst presence.
    monkeypatch.setattr(snippet_injector, "_try_parse_python_with_libcst", lambda _: None)
    monkeypatch.setattr(snippet_injector, "_find_python_anchor_line_with_libcst", lambda *_: 0)

    called = {"black": 0}

    def _fake_format_with_black(text: str):
        called["black"] += 1
        return ("BLACK_WOULD_HAVE_CHANGED_THIS\n", None)

    monkeypatch.setattr(snippet_injector, "_format_with_black", _fake_format_with_black)

    target = tmp_path / "app.py"
    target.write_text("# <<<inject:settings-fields>>>\n", encoding="utf-8")

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
            # patch_mode intentionally omitted
        },
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is True
    assert called["black"] == 0


def test_default_patch_mode_non_python_still_formats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    called = {"black": 0}

    def _fake_format_with_black(text: str):
        called["black"] += 1
        return (text, None)

    monkeypatch.setattr(snippet_injector, "_format_with_black", _fake_format_with_black)

    target = tmp_path / "app.ts"
    target.write_text("// <<<inject:settings-fields>>>\n", encoding="utf-8")

    tpl = tmp_path / "t.j2"
    tpl.write_text("const X = 1\n", encoding="utf-8")

    res = snippet_injector.inject_snippet_enterprise(
        destination_path=target,
        template_path=tpl,
        anchor="// <<<inject:settings-fields>>>",
        variables={},
        snippet_metadata={
            "id": "x",
            "version": "1.0.0",
            "priority": 1,
            "template": "t.j2",
            "module_slug": "free/database/db_postgres",
            "context": {},
            "conflict_resolution": "override",
            # patch_mode intentionally omitted
        },
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is True
    assert called["black"] == 1
