from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.services import snippet_injector


def test_ast_py_mode_skips_black_formatting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "app.py"
    target.write_text("# <<<inject:settings-fields>>>\n", encoding="utf-8")

    tpl = tmp_path / "t.j2"
    tpl.write_text("X=1\n", encoding="utf-8")

    called = {"count": 0}

    def _fake_format_with_black(text: str):
        called["count"] += 1
        return ("BLACK_WOULD_HAVE_CHANGED_THIS\n", None)

    monkeypatch.setattr(snippet_injector, "_format_with_black", _fake_format_with_black)

    # Avoid dependency on libcst presence by forcing parse helper to succeed.
    monkeypatch.setattr(snippet_injector, "_try_parse_python_with_libcst", lambda _: None)

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


def test_ast_py_marks_conflicted_when_libcst_parse_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "app.py"
    target.write_text("# <<<inject:settings-fields>>>\n", encoding="utf-8")

    tpl = tmp_path / "t.j2"
    # This is fine; we'll simulate libcst parse failure regardless.
    tpl.write_text("X = 1\n", encoding="utf-8")

    monkeypatch.setattr(snippet_injector, "_try_parse_python_with_libcst", lambda _: "boom")

    before = target.read_text(encoding="utf-8")
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

    assert res["injected"] is False
    assert res["blocked"] is True
    assert target.read_text(encoding="utf-8") == before

    reg = json.loads((tmp_path / ".rapidkit" / "snippet_registry.json").read_text(encoding="utf-8"))
    assert reg["snippets"]["x::app.py"]["status"] == "conflicted"


def test_inject_python_snippet_ast_strips_trailing_newlines_in_snippet_lines():
    source = (
        "from pydantic import BaseSettings\n"
        "\n"
        "class Settings(BaseSettings):\n"
        "    # <<<inject:settings-fields>>>\n"
        "    pass\n"
    )

    new_source, err = snippet_injector._inject_python_snippet_ast(
        source=source,
        anchor_stripped="# <<<inject:settings-fields>>>",
        snippet_id="demo",
        snippet_lines=["X = 1\n", "Y = 2\n"],
        indent="    ",
        prefix="# ",
    )
    assert err is None
    assert new_source is not None
    assert "X = 1\n\n" not in new_source
    assert "Y = 2\n\n" not in new_source
    assert "X = 1\n    Y = 2\n" in new_source


def test_inject_python_snippet_ast_replace_block_strips_trailing_newlines_in_snippet_lines():
    source = (
        "class Settings:\n"
        "    # <<<inject:settings-fields>>>\n"
        "    # <<<inject:settings-fields:demo:start>>>\n"
        "    A = 0\n"
        "    # <<<inject:settings-fields:demo:end>>>\n"
    )

    new_source, err = snippet_injector._inject_python_snippet_ast(
        source=source,
        anchor_stripped="# <<<inject:settings-fields>>>",
        snippet_id="demo",
        snippet_lines=["X = 1\n", "Y = 2\n"],
        indent="    ",
        prefix="# ",
    )
    assert err is None
    assert new_source is not None
    assert "X = 1\n\n" not in new_source
    assert "Y = 2\n\n" not in new_source
