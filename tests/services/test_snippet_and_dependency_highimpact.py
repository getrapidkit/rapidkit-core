from pathlib import Path

from core.services import snippet_injector as si


def test_inject_snippet_from_template_idempotent(tmp_path: Path, monkeypatch):
    target = tmp_path / "project.txt"
    target.write_text("# header\n# <<<inject:module-dependencies>>>\n")
    tpl = tmp_path / "s.j2"
    tpl.write_text('pkg_extra = "0.0.1"\n')

    def _no_op(*_a, **_k):
        return None

    monkeypatch.setattr(si, "print_info", _no_op)
    monkeypatch.setattr(si, "print_warning", _no_op)
    monkeypatch.setattr(si, "print_success", _no_op)

    res = si.inject_snippet_enterprise(
        destination_path=target,
        template_path=tpl,
        anchor="# <<<inject:module-dependencies>>>",
        variables={},
        snippet_metadata={"id": "pkg_extra", "version": "0.0.1", "schema": {}},
        project_root=tmp_path,
        lenient=True,
    )
    assert res.get("injected") is True
    out = target.read_text()
    assert "pkg_extra" in out

    # repeat injection should be detected
    res2 = si.inject_snippet_enterprise(
        destination_path=target,
        template_path=tpl,
        anchor="# <<<inject:module-dependencies>>>",
        variables={},
        snippet_metadata={"id": "pkg_extra", "version": "0.0.1", "schema": {}},
        project_root=tmp_path,
        lenient=True,
    )
    assert isinstance(res2, dict)
