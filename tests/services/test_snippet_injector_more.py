import re
from pathlib import Path

from core.services import snippet_injector as si


def test_filter_updates_preserve_base_and_merge(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    content = """[tool.poetry.dependencies]
python = "^3.11"
alpha = "0.1.0"
# <<<inject:module-dependencies>>>
beta = "0.2.0"

"""
    py.write_text(content)
    # snippet tries to add gamma and also attempts to overwrite alpha (should not touch base alpha)
    snippet = 'gamma = "^1.0.0"\nalpha = "^9.9.9"'
    out = si.filter_and_update_poetry_dependencies_snippet(py, snippet)
    # header preserved
    assert "[tool.poetry.dependencies]" in out
    # base alpha must remain present in base section (not overwritten)
    assert re.search(r'alpha\s*=\s*"0.1.0"', out)
    # gamma must be present in injected block
    assert "gamma" in out
    # anchor must exist
    assert "# <<<inject:module-dependencies>>>" in out


def test_filter_appends_section_when_missing(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    py.write_text("[tool.other]\nkey=1\n")
    snippet = 'pkg = "0.0.1"'
    out = si.filter_and_update_poetry_dependencies_snippet(py, snippet)
    assert "[tool.poetry.dependencies]" in out
    assert "pkg" in out
