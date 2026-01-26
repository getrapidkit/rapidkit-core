import yaml

from cli.utils import module_scaffold
from cli.utils.module_scaffold import ModuleScaffolder
from cli.utils.scaffold.constants import (
    REPOSITORY_INTEGRATION_SUFFIX,
    REPOSITORY_TEST_SUFFIXES,
)


def test_create_module_expands_templates(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    modules_root = repo_root / "src" / "modules"
    modules_root.mkdir(parents=True)

    original_repo_root = module_scaffold.REPO_ROOT
    original_modules_root = module_scaffold.MODULES_ROOT
    monkeypatch.setattr(module_scaffold, "REPO_ROOT", repo_root)
    monkeypatch.setattr(module_scaffold, "MODULES_ROOT", modules_root)

    scaffolder = ModuleScaffolder(modules_root=modules_root)
    result = scaffolder.create_module(
        tier="free",
        category="essentials",
        module_name="alpha",
        description="Test module",
    )

    created = result.created_files
    assert len(created) == len(set(created)), "Duplicate files detected"
    assert all("$" not in str(path) for path in created)

    module_root = modules_root / "free" / "essentials" / "alpha"
    assert (module_root / "module.yaml").exists()
    assert (module_root / "generate.py").exists()

    test_dir = repo_root / "tests" / "modules" / "free" / "essentials" / "alpha"
    expected_tests = {f"test_alpha_{name}.py" for name in REPOSITORY_TEST_SUFFIXES}
    assert {path.name for path in test_dir.iterdir()} == expected_tests | {
        "__init__.py",
        "conftest.py",
    }

    integration_dir = (
        repo_root / "tests" / "modules" / "free" / "integration" / "essentials" / "alpha"
    )
    assert (integration_dir / "__init__.py").exists()
    assert (integration_dir / f"test_alpha_{REPOSITORY_INTEGRATION_SUFFIX}.py").exists()

    expected_unit_tests = [
        f"tests/modules/free/essentials/alpha/test_alpha_{name}.py"
        for name in REPOSITORY_TEST_SUFFIXES
    ]

    module_yaml = yaml.safe_load((module_root / "module.yaml").read_text(encoding="utf-8"))
    assert module_yaml["testing"]["unit_tests"] == expected_unit_tests
    assert module_yaml["testing"]["integration_tests"] is True
    assert module_yaml["testing"]["integration_test_files"] == [
        "tests/modules/free/integration/essentials/alpha/test_alpha_integration.py"
    ]

    docs_root = module_root / "docs"
    for name in ("overview", "usage", "advanced", "migration", "troubleshooting", "api-reference"):
        assert (docs_root / f"{name}.md").exists()

    # restore globals for any code inspecting the module later in the test suite
    module_scaffold.REPO_ROOT = original_repo_root
    module_scaffold.MODULES_ROOT = original_modules_root
