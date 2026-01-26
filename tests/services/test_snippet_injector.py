from pathlib import Path

from core.services import snippet_injector as si
from core.services.snippet_injector import inject_snippet_enterprise


def test_parse_poetry_dependency_line_basic():
    cases = [
        ('package = "1.2.3"', ("package", '"1.2.3"')),
        ("  package='^1.0'  # comment", ("package", "'^1.0'")),
        ("# comment", (None, None)),
        ("not a dep", (None, None)),
        (
            'pkg = { version = "1.2", extras=["a"] }',
            ("pkg", '{ version = "1.2", extras=["a"] }'),
        ),
    ]
    for inp, exp in cases:
        assert si.parse_poetry_dependency_line(inp) == exp


def test_filter_and_update_poetry_dependencies_snippet_new_section(tmp_path: Path):
    p = tmp_path / "pyproject.toml"
    p.write_text("[tool.other]\nkey = 1\n")
    snippet = 'alpha = "0.1.0"\nbeta = "^2.0.0"'
    new = si.filter_and_update_poetry_dependencies_snippet(p, snippet)
    assert "[tool.poetry.dependencies]" in new
    assert "# <<<inject:module-dependencies>>>" in new
    assert "alpha" in new and "beta" in new


def test_inject_requirements_and_remove_anchor_and_load_registry(tmp_path: Path):
    req = tmp_path / "requirements.txt"
    content = "# header\n# <<<inject:module-dependencies>>>\n"
    req.write_text(content)
    snippet = "packageA==1.0.0\npackageB==2.0.0"
    updated = si.inject_dependencies(req, snippet, file_type="requirements")
    assert "packageA==1.0.0" in updated
    # writing updated content to file simulation
    req.write_text(updated)
    # remove anchors in-place
    si.remove_inject_anchors(req)
    post = req.read_text()
    assert "<<<inject:module-dependencies>>>" not in post

    # corrupted registry should be handled
    reg = tmp_path / ".rapidkit" / "snippet_registry.json"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text("not-a-json")
    loaded = si.load_snippet_registry(tmp_path)
    assert isinstance(loaded, dict)
    assert loaded.get("snippets") == {}


def test_inject_snippet_env_lenient(tmp_path: Path):
    target = tmp_path / ".env"
    target.write_text("# anchor\n# <<<inject:ENV-ANCHOR>>>\n", encoding="utf-8")
    snippet_template = tmp_path / "snippet.env"
    snippet_template.write_text("MY_KEY=123\n", encoding="utf-8")

    res = inject_snippet_enterprise(
        destination_path=target,
        template_path=snippet_template,
        anchor="# <<<inject:ENV-ANCHOR>>>",
        variables={},
        snippet_metadata={"id": "env-test", "version": "0.0.1"},
        project_root=tmp_path,
        lenient=True,
    )
    assert res["injected"] is True and res["blocked"] is False
    new_content = target.read_text(encoding="utf-8")
    assert "MY_KEY" in new_content


def test_inject_snippet_missing_anchor_blocks(tmp_path: Path):
    target = tmp_path / "settings.py"
    target.write_text("# no anchor here\n", encoding="utf-8")
    snippet_template = tmp_path / "snippet.py.j2"
    snippet_template.write_text("print('hi')\n", encoding="utf-8")

    res = inject_snippet_enterprise(
        destination_path=target,
        template_path=snippet_template,
        anchor="# <<<inject:missing-anchor>>>",
        variables={},
        snippet_metadata={"id": "missing-anchor", "version": "1.0.0"},
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is False
    assert res["blocked"] is True
    errors_obj = res.get("errors")
    assert isinstance(errors_obj, list)
    assert any("anchor" in str(err) for err in errors_obj)
    assert target.read_text(encoding="utf-8").strip() == "# no anchor here"


def test_inject_snippet_respects_metadata_context(tmp_path: Path):
    target = tmp_path / "settings.py"
    target.write_text("# <<<inject:settings-fields>>>\n", encoding="utf-8")
    snippet_template = tmp_path / "snippet.py.j2"
    snippet_template.write_text(
        """{% if fragment == 'settings' %}class Injected: ... {{ suffix }}{% endif %}\n""",
        encoding="utf-8",
    )

    res = inject_snippet_enterprise(
        destination_path=target,
        template_path=snippet_template,
        anchor="# <<<inject:settings-fields>>>",
        variables={"suffix": "#ok"},
        snippet_metadata={
            "id": "context-fragment",
            "version": "1.0.0",
            "context": {"fragment": "settings"},
        },
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is True
    output = target.read_text(encoding="utf-8")
    assert "Injected" in output
    assert "ok" in output


def test_inject_snippet_registry_stored_under_rapidkit_dir(tmp_path: Path):
    nested = tmp_path / "src" / "config"
    nested.mkdir(parents=True)
    target = nested / "settings.ts"
    target.write_text("// <<<inject:settings-fields>>>\n", encoding="utf-8")
    snippet_template = tmp_path / "snippet.ts.j2"
    snippet_template.write_text("export const enabled = true;\n", encoding="utf-8")

    res = inject_snippet_enterprise(
        destination_path=target,
        template_path=snippet_template,
        anchor="// <<<inject:settings-fields>>>",
        variables={},
        snippet_metadata={"id": "ts-fields", "version": "1.2.3"},
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is True
    registry_path = tmp_path / ".rapidkit" / "snippet_registry.json"
    nested_registry = nested / "snippet_registry.json"
    assert registry_path.exists()
    assert not nested_registry.exists()
    data = registry_path.read_text(encoding="utf-8")
    assert "src/config/settings.ts" in data
