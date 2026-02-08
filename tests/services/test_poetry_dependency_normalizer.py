from pathlib import Path

from core.services.poetry_dependency_normalizer import (
    _parse_key_value_lines,
    _split_sections,
    _strip_inline_comment,
    normalize_poetry_dependencies,
)


def test_normalize_moves_dev_tools_to_dev_section(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.poetry]
name = "sample"

[tool.poetry.dependencies]
python = "^3.10"
pytest = "^7.0" # should move
black = "^23.0"
requests = "^2.0"
pydantic = { version = "^2.0", extras = ["email"] }

[tool.poetry.group.dev.dependencies]
pytest = "^7.1"
mypy = "^1.0"

[build-system]
requires = ["poetry-core"]
""".lstrip(),
        encoding="utf-8",
    )

    changed = normalize_poetry_dependencies(pyproject)
    assert changed is True

    updated = pyproject.read_text(encoding="utf-8")
    sections = _split_sections(updated)
    main_deps = _parse_key_value_lines(sections["tool.poetry.dependencies"][0])
    dev_deps = _parse_key_value_lines(sections["tool.poetry.group.dev.dependencies"][0])

    assert "pytest" not in main_deps
    assert "black" not in main_deps
    assert main_deps["python"] == '"^3.10"'
    assert main_deps["requests"] == '"^2.0"'
    assert "pydantic" in main_deps

    assert dev_deps["pytest"] == '"^7.1"'
    assert dev_deps["black"] == '"^23.0"'
    assert dev_deps["mypy"] == '"^1.0"'


def test_normalize_inserts_dev_section_before_build_system(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.poetry]
name = "sample"

[tool.poetry.dependencies]
python = "^3.10"
ruff = "^0.3.0"

[build-system]
requires = ["poetry-core"]
""".lstrip(),
        encoding="utf-8",
    )

    changed = normalize_poetry_dependencies(pyproject)
    assert changed is True

    updated = pyproject.read_text(encoding="utf-8")
    assert "[tool.poetry.group.dev.dependencies]" in updated
    assert updated.index("[tool.poetry.group.dev.dependencies]") < updated.index("[build-system]")

    sections = _split_sections(updated)
    main_deps = _parse_key_value_lines(sections["tool.poetry.dependencies"][0])
    dev_deps = _parse_key_value_lines(sections["tool.poetry.group.dev.dependencies"][0])

    assert "ruff" not in main_deps
    assert dev_deps["ruff"] == '"^0.3.0"'


def test_strip_inline_comment_respects_quotes() -> None:
    assert _strip_inline_comment('"value#1" # trailing') == '"value#1"'
    assert _strip_inline_comment("'value#2' # trailing") == "'value#2'"
    assert _strip_inline_comment("value # trailing") == "value"
