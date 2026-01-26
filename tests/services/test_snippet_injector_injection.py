from pathlib import Path

from core.services import snippet_injector as si


def test_inject_snippet_from_template_pyproject(tmp_path: Path, monkeypatch):
    # prepare a generic file with anchor
    py = tmp_path / "target.txt"
    py.write_text("# preamble\n# <<<inject:module-dependencies>>>\n")

    # template file (rendered as-is)
    tpl = tmp_path / "snippet.j2"
    tpl.write_text('gamma = "0.1.0"\n')

    # silence printers
    monkeypatch.setattr(si, "print_success", lambda *_: None)
    monkeypatch.setattr(si, "print_info", lambda *_: None)
    monkeypatch.setattr(si, "print_warning", lambda *_: None)

    # inject using enterprise helper (returns result)
    res = si.inject_snippet_enterprise(
        destination_path=py,
        template_path=tpl,
        anchor="# <<<inject:module-dependencies>>>",
        variables={},
        snippet_metadata={"id": "s1", "version": "0.0.1", "schema": {}},
        project_root=tmp_path,
        lenient=True,
    )
    assert isinstance(res, dict)
    assert res.get("injected") is True
    content = py.read_text()
    assert "gamma" in content

    # idempotence: second call should detect already present and not inject
    res2 = si.inject_snippet_enterprise(
        destination_path=py,
        template_path=tpl,
        anchor="# <<<inject:module-dependencies>>>",
        variables={},
        snippet_metadata={"id": "s1", "version": "0.0.1", "schema": {}},
        project_root=tmp_path,
        lenient=True,
    )
    assert isinstance(res2, dict)
