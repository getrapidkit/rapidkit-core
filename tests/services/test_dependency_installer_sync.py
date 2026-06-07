from pathlib import Path

from core.engine import dependency_installer as di


def test_parse_poetry_dependencies_section_and_sync(tmp_path: Path):
    py = tmp_path / "pyproject.toml"
    py.write_text("""[tool.poetry.dependencies]
python = "^3.11"
alpha = "^1.0.0"
# <<<inject:module-dependencies>>>
beta = "^0.2.0"

""")
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


def test_lock_sync_skip_env_skips_poetry_and_npm_subprocesses(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(cmd, **_kwargs):
        calls.append(list(cmd))
        raise AssertionError("lock sync subprocess should be skipped")

    monkeypatch.setenv("RAPIDKIT_SKIP_LOCK_SYNC", "1")
    monkeypatch.setattr(di.subprocess, "run", _fake_run)

    (tmp_path / "pyproject.toml").write_text("[tool.poetry.dependencies]\npython = '^3.10'\n")
    (tmp_path / "poetry.lock").write_text("# lock\n")
    di._sync_poetry_lockfile(tmp_path)

    (tmp_path / "package.json").write_text('{"dependencies": {}}\n')
    (tmp_path / "package-lock.json").write_text('{"lockfileVersion": 3}\n')
    di._sync_npm_lockfile(tmp_path)

    assert calls == []
