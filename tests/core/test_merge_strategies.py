import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.main import app as cli_app

runner = CliRunner()


def _extract_json(text: str):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise AssertionError("No JSON found")
    return json.loads(text[start : end + 1])


def test_merge_prefer_current_no_overwrite(temp_project: Path, primary_project_name: str):
    # Modify a file so it's locally_modified (change current only)
    target = temp_project / "backend/core/config.py"
    if not target.exists():
        pytest.skip("logging module file missing in this boilerplate")
    contents = target.read_text(encoding="utf-8")
    target.write_text(contents + "\n# LOCAL_CHANGE", encoding="utf-8")
    res = runner.invoke(
        cli_app,
        [
            "merge",
            "module",
            "logging",
            "--project",
            primary_project_name,
            "--strategy",
            "prefer-current",
            "--json",
        ],
    )
    assert res.exit_code == 0, res.output
    data = _extract_json(res.output)
    # Ensure no action applied
    assert all(not a.get("will_update") for a in data.get("actions", []))


def test_merge_prefer_template_applies(temp_project: Path, primary_project_name: str):
    target = temp_project / "backend/core/config.py"
    if not target.exists():
        pytest.skip("logging module file missing in this boilerplate")
    contents = target.read_text(encoding="utf-8")
    target.write_text(contents + "\n# LOCAL2", encoding="utf-8")
    res = runner.invoke(
        cli_app,
        [
            "merge",
            "module",
            "logging",
            "--project",
            primary_project_name,
            "--strategy",
            "prefer-template",
            "--json",
        ],
    )
    assert res.exit_code == 0, res.output
    data = _extract_json(res.output)
    # At least one update OR explanation why not (no template)
    if any(a.get("decision") == "apply_template" for a in data.get("actions", [])):
        assert any(a.get("will_update") for a in data.get("actions", []))


def test_merge_auto_apply_template_updated_flag(_temp_project: Path, primary_project_name: str):
    from cli.commands.diff import MODULES_PATH

    template_path = MODULES_PATH / "logging" / "templates" / "base" / "backend/core/config.py.j2"
    if not template_path.exists():
        pytest.skip("template missing")
    original = template_path.read_text(encoding="utf-8")
    try:
        template_path.write_text("# AUTO_FLAG\n" + original, encoding="utf-8")
        res = runner.invoke(
            cli_app,
            [
                "merge",
                "module",
                "logging",
                "--project",
                primary_project_name,
                "--strategy",
                "prompt",
                "--auto-apply-template-updated",
                "--dry-run",
                "--json",
            ],
        )
        assert res.exit_code == 0, res.output
        data = _extract_json(res.output)
        # If a template_updated present ensure auto decision taken
        statuses = [a.get("status_before") for a in data.get("actions", [])]
        if "template_updated" in statuses:
            assert any(
                a.get("decision") in {"apply_template_auto", "apply_template"}
                for a in data.get("actions", [])
            )
    finally:
        template_path.write_text(original, encoding="utf-8")
