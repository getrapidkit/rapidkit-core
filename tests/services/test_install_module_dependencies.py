from pathlib import Path

from core.engine import dependency_installer as di


def test_install_module_dependencies_writes_files(tmp_path: Path, monkeypatch):
    # Prepare project files
    py = tmp_path / "pyproject.toml"
    py.write_text('[tool.poetry.dependencies]\npython = "^3.11"\n')
    registry = tmp_path / "registry.json"
    registry.write_text('{"installed_modules": ["localmod"]}')

    config = {
        "depends_on": {
            "dev": [
                {"name": "extpkg", "version": "^1.2.3", "source": "external"},
                {"name": "localmod", "source": "local"},
            ]
        },
        "dev_dependencies": [{"name": "pytest", "version": "*", "source": "external"}],
    }

    # Patch find_project_root and normalization
    def _fake_find_project_root(*_a, **_k):
        return tmp_path

    def _fake_normalize_poetry_dependencies(*_a, **_k):
        return True

    monkeypatch.setattr(di, "find_project_root", _fake_find_project_root)
    monkeypatch.setattr(di, "normalize_poetry_dependencies", _fake_normalize_poetry_dependencies)

    # Run installer
    di.install_module_dependencies(config, profile="dev", project="myproj", final=False)

    # Expect pyproject updated with extpkg (requirements.txt sync removed in Poetry-first approach)
    txt = py.read_text()
    assert "extpkg" in txt
    # Note: requirements.txt sync is no longer performed in Poetry-first workflow
    # req_file = tmp_path / "requirements" / "requirements.txt"
    # assert req_file.exists()
    # reqtxt = req_file.read_text()
    # assert "extpkg" in reqtxt


def test_install_module_dependencies_no_project_root(monkeypatch):
    monkeypatch.setattr(di, "find_project_root", lambda *_a, **_k: None)
    # Should not raise
    di.install_module_dependencies({}, profile="dev", project="x", final=True)


def test_install_module_dependencies_respects_profile_inheritance(
    tmp_path: Path, monkeypatch
) -> None:
    py = tmp_path / "pyproject.toml"
    py.write_text('[tool.poetry.dependencies]\npython = "^3.11"\n')

    config = {
        "profiles": {
            "fastapi/ddd": {"inherits": "fastapi/standard"},
            "fastapi/standard": {},
        },
        "depends_on": {
            "fastapi/standard": [{"name": "stdpkg", "version": "^1.0", "source": "external"}],
            "fastapi/ddd": [{"name": "dddpkg", "version": "^2.0", "source": "external"}],
        },
    }

    def _fake_find_project_root(*_a, **_k):
        return tmp_path

    def _fake_normalize_poetry_dependencies(*_a, **_k):
        return False

    monkeypatch.setattr(di, "find_project_root", _fake_find_project_root)
    monkeypatch.setattr(di, "normalize_poetry_dependencies", _fake_normalize_poetry_dependencies)

    di.install_module_dependencies(
        config,
        profile="fastapi/ddd",
        project="proj",
        final=False,
    )

    contents = py.read_text()
    assert "stdpkg" in contents
    assert "dddpkg" in contents
