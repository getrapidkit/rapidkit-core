from pathlib import Path

import pytest

from core.config.kit_config import KitConfig, StructureItem, Variable, VariableType
from core.engine.generator import BaseKitGenerator
from core.exceptions import ValidationError


class SimpleKitGenerator(BaseKitGenerator):
    def extra_context(self) -> dict[str, str]:  # minimal extra context
        return {"extra": "ok"}


def _make_config(_kit_path: Path) -> KitConfig:
    return KitConfig(
        name="testkit",
        display_name="Test Kit",
        description="Testing kit",
        version="0.1.0",
        min_rapidkit_version="0.0.1",
        category="test",
        tags=[],
        dependencies={},
        modules=[],
        variables=[
            Variable(name="project_name", type=VariableType.STRING, required=True),
            Variable(
                name="license",
                type=VariableType.CHOICE,
                required=False,
                default="mit",
                choices=["mit", "apache"],
            ),
        ],
        structure=[
            StructureItem(path="README.md", template="README.md.j2"),
            StructureItem(
                path="LICENSE.txt",
                template_if={"mit": "LICENSE_MIT.j2", "apache": "LICENSE_APACHE.j2"},
            ),
            StructureItem(path="empty_dir/"),
        ],
        hooks={},
    )


@pytest.fixture()
def kit_dir(tmp_path: Path) -> Path:
    kt = tmp_path / "kit"
    templates = kt / "templates"
    templates.mkdir(parents=True)
    (templates / "README.md.j2").write_text(
        "# {{ project_name }}\nExtra={{ extra }}", encoding="utf-8"
    )
    (templates / "LICENSE_MIT.j2").write_text("MIT LICENSE", encoding="utf-8")
    (templates / "LICENSE_APACHE.j2").write_text("APACHE LICENSE", encoding="utf-8")
    return kt


def test_generator_creates_files_and_renders_variables(kit_dir: Path, tmp_path: Path) -> None:
    cfg = _make_config(kit_dir)
    gen = SimpleKitGenerator(kit_dir, cfg)
    out = tmp_path / "out"
    out.mkdir()
    files = gen.generate(out, {"project_name": "demo", "license": "mit"})
    readme = (out / "README.md").read_text(encoding="utf-8")
    license_txt = (out / "LICENSE.txt").read_text(encoding="utf-8")
    assert "demo" in readme and "Extra=ok" in readme
    assert "MIT LICENSE" in license_txt
    # Directory creation
    assert (out / "empty_dir").is_dir()
    # Returned file list includes created files (non-directories)
    assert any(str(out / "README.md") == f for f in files)


def test_generator_template_if_branch_selects_template(kit_dir: Path, tmp_path: Path) -> None:
    cfg = _make_config(kit_dir)
    gen = SimpleKitGenerator(kit_dir, cfg)
    out = tmp_path / "out2"
    out.mkdir()
    gen.generate(out, {"project_name": "demo2", "license": "apache"})
    license_txt = (out / "LICENSE.txt").read_text(encoding="utf-8")
    assert "APACHE LICENSE" in license_txt


def test_generator_missing_required_variable_raises(kit_dir: Path, tmp_path: Path) -> None:
    cfg = _make_config(kit_dir)
    gen = SimpleKitGenerator(kit_dir, cfg)
    out = tmp_path / "out3"
    out.mkdir()
    with pytest.raises(ValidationError):
        gen.generate(out, {"license": "mit"})  # project_name missing
