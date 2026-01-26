from pathlib import Path

from core.engine import dependency_installer as di


def test_parse_poetry_dependencies_section_and_sync(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    py.write_text(
        """[tool.poetry.dependencies]
python = "^3.11"
alpha = "^1.0.0"
# <<<inject:module-dependencies>>>
beta = "^0.2.0"

"""
    )
    parsed = di._parse_poetry_dependencies_section(py.read_text())
    assert parsed is not None
    section, base, injected = parsed
    # alpha should appear in base and beta in injected
    assert any(n == "alpha" for n, _ in base)
    assert any(n == "beta" for n, _ in injected)

    # Now test syncing produces requirements file
    req_dir = tmp_path / "requirements"
    req_file = req_dir / "requirements.txt"
    di._sync_requirements_full_from_pyproject(req_file, py)
    assert req_file.exists()
    txt = req_file.read_text()
    assert "alpha" in txt and "beta" in txt
    # caret ^ should be expanded to range in requirements
    assert ">=" in txt
