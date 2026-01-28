from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pytest

from core.exceptions import RapidKitError, ValidationError
from core.services.project_creator import ProjectCreatorService


@dataclass
class DummyVar:
    name: str
    required: bool = False
    default: Any = None


@pytest.fixture()
def project_creator() -> ProjectCreatorService:
    return ProjectCreatorService()


def test_parse_variables_valid(project_creator: ProjectCreatorService) -> None:
    result = project_creator._parse_variables(["key=value", "flag=yes"])  # noqa: SLF001
    assert result == {"key": "value", "flag": "yes"}


def test_parse_variables_invalid(project_creator: ProjectCreatorService) -> None:
    with pytest.raises(ValidationError):
        project_creator._parse_variables(["invalid"])  # noqa: SLF001


def test_get_run_command_poetry_available(monkeypatch: pytest.MonkeyPatch) -> None:
    pc = ProjectCreatorService()

    def _fake_run(*_args: Any, **_kwargs: Any) -> None:
        return None

    monkeypatch.setattr("subprocess.run", _fake_run)
    # project creator now prefers the canonical `rapidkit dev` developer flow
    assert pc._get_run_command_for_kit("fastapi.standard") == "rapidkit dev"  # noqa: SLF001


def test_get_run_command_poetry_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    pc = ProjectCreatorService()

    def _raise(*_args: Any, **_kwargs: Any) -> None:
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", _raise)
    # Even if Poetry is missing, the canonical run command for created projects
    # is `rapidkit dev` (the CLI will fallback to an appropriate runner when used).
    assert pc._get_run_command_for_kit("fastapi.standard") == "rapidkit dev"  # noqa: SLF001


def test_get_next_steps_for_nestjs(monkeypatch: pytest.MonkeyPatch) -> None:
    pc = ProjectCreatorService()

    def _fake_run_command(_kit: str, vars: Dict[str, Any] | None = None) -> str:
        vars = vars or {}
        return f"run-{vars.get('package_manager', 'npm')}"

    monkeypatch.setattr(pc, "_get_run_command_for_kit", _fake_run_command)
    steps = pc._get_next_steps_for_kit(
        "nestjs.default", {"package_manager": "yarn"}
    )  # noqa: SLF001
    assert steps[:3] == [
        "source .rapidkit/activate",
        "rapidkit init",
        "./bootstrap.sh",
    ]
    assert steps[-1] == "run-yarn"


def test_apply_kit_defaults_merges_only_missing(project_creator: ProjectCreatorService) -> None:
    kit = type("Kit", (), {"variables": [DummyVar("color", default="blue"), DummyVar("size")]})
    vars = {"size": "L"}
    merged = project_creator._apply_kit_defaults(kit, vars)  # noqa: SLF001
    assert merged == {"size": "L", "color": "blue"}


def test_install_essential_modules_handles_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pc = ProjectCreatorService()

    calls: Dict[str, int] = {"run": 0}

    def _fake_run(cmd: list[str], **_kwargs: Any) -> Any:
        calls["run"] += 1
        if "free/essentials/settings" in cmd:

            class _Result:
                returncode = 0
                stdout = ""
                stderr = ""

            return _Result()
        if "free/essentials/logging" in cmd:
            raise subprocess.TimeoutExpired(cmd, timeout=300)
        raise RuntimeError("unexpected module")

    monkeypatch.setattr("shutil.which", lambda _name: "rapidkit")
    monkeypatch.setattr("subprocess.run", _fake_run)
    info_messages: list[str] = []
    success_messages: list[str] = []
    error_messages: list[str] = []

    pc._install_essential_modules(
        tmp_path,
        "fastapi/standard",
        info_messages.append,
        success_messages.append,
        error_messages.append,
    )

    expected_run_calls = 4
    assert any("free/essentials/settings" in msg for msg in success_messages)
    assert any("Timeout" in msg for msg in error_messages)
    assert any("free/essentials/deployment" in msg for msg in error_messages)
    assert calls["run"] == expected_run_calls


def test_create_project_missing_kit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pc = ProjectCreatorService()
    monkeypatch.setattr(pc.registry, "list_kits_names", lambda: ["fastapi.standard"])

    class _DummyKit:
        variables: list[Any] = []
        min_rapidkit_version = "0.0.1"
        display_name = "Demo Kit"
        description = "desc"

    monkeypatch.setattr(pc.registry, "get_kit", lambda *_a, **_k: _DummyKit())

    class _DummyGenerator:
        def generate(self, *_args: Any, **_kwargs: Any) -> list[str]:
            return []

    monkeypatch.setattr(pc.registry, "get_generator", lambda *_a, **_k: _DummyGenerator())

    with pytest.raises(RapidKitError):
        pc.create_project(
            kit_name="unknown",
            project_name="Proj",
            output_dir=tmp_path,
            variables={},
            force=True,
            interactive=False,
            debug=False,
            prompt_func=None,
            print_funcs={
                "info": lambda *_a: None,
                "error": lambda *_a: None,
                "success": lambda *_a: None,
            },
            install_essential_modules=False,
        )


def test_create_project_skips_essential_when_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ensure create_project does not run the essential-module installer when asked to skip."""
    pc = ProjectCreatorService()

    # Minimal registry kit stubs
    monkeypatch.setattr(pc.registry, "list_kits_names", lambda: ["fastapi.standard"])

    class _DummyKit:
        variables: list[Any] = []
        min_rapidkit_version = "0.0.1"
        display_name = "Demo Kit"
        description = "desc"

    monkeypatch.setattr(pc.registry, "get_kit", lambda *_a, **_k: _DummyKit())

    # Generator that reports a couple of created paths
    class _DummyGenerator:
        def generate(self, *_args: Any, **_kwargs: Any) -> list[str]:
            return ["/tmp/proj/src/main.py", "/tmp/proj/README.md"]

    monkeypatch.setattr(pc.registry, "get_generator", lambda *_a, **_k: _DummyGenerator())

    called = {"install_called": False}

    def _fake_install(*_args: Any, **_kwargs: Any) -> None:
        called["install_called"] = True

    # patch the installer so we can detect calls
    monkeypatch.setattr(pc, "_install_essential_modules", _fake_install)

    created = pc.create_project(
        kit_name="fastapi.standard",
        project_name="Proj",
        output_dir=tmp_path,
        variables={},
        force=True,
        interactive=False,
        debug=False,
        prompt_func=None,
        print_funcs={
            "info": lambda *_a: None,
            "error": lambda *_a: None,
            "success": lambda *_a: None,
        },
        install_essential_modules=False,
    )

    # Ensure the fake installer was not invoked
    assert called["install_called"] is False
    # Confirm the generator returned the expected converted Paths
    assert all(
        p.as_posix().endswith("src/main.py") or p.as_posix().endswith("README.md") for p in created
    )


def test_create_project_writes_required_rapidkit_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pc = ProjectCreatorService()

    monkeypatch.setattr(pc.registry, "list_kits_names", lambda: ["fastapi.standard"])

    class _DummyKit:
        variables: list[Any] = []
        min_rapidkit_version = "0.0.1"
        display_name = "Demo Kit"
        description = "desc"

    monkeypatch.setattr(pc.registry, "get_kit", lambda *_a, **_k: _DummyKit())

    class _DummyGenerator:
        def generate(self, out: Path, *_args: Any, **_kwargs: Any) -> list[str]:
            # Intentionally do not create `.rapidkit/`; the service must still create it via metadata.
            (out / "README.md").parent.mkdir(parents=True, exist_ok=True)
            (out / "README.md").write_text("demo", encoding="utf-8")
            return [str(out / "README.md")]

    monkeypatch.setattr(pc.registry, "get_generator", lambda *_a, **_k: _DummyGenerator())

    pc.create_project(
        kit_name="fastapi.standard",
        project_name="Proj",
        output_dir=tmp_path,
        variables={},
        force=True,
        interactive=False,
        debug=False,
        prompt_func=None,
        print_funcs={
            "info": lambda *_a: None,
            "error": lambda *_a: None,
            "success": lambda *_a: None,
        },
        install_essential_modules=False,
    )

    assert (tmp_path / "Proj" / ".rapidkit" / "project.json").exists()


def test_create_project_fails_if_metadata_cannot_be_written(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pc = ProjectCreatorService()

    monkeypatch.setattr(pc.registry, "list_kits_names", lambda: ["fastapi.standard"])

    class _DummyKit:
        variables: list[Any] = []
        min_rapidkit_version = "0.0.1"
        display_name = "Demo Kit"
        description = "desc"

    monkeypatch.setattr(pc.registry, "get_kit", lambda *_a, **_k: _DummyKit())

    class _DummyGenerator:
        def generate(self, out: Path, *_args: Any, **_kwargs: Any) -> list[str]:
            out.mkdir(parents=True, exist_ok=True)
            return []

    monkeypatch.setattr(pc.registry, "get_generator", lambda *_a, **_k: _DummyGenerator())

    def _fail_save(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("nope")

    monkeypatch.setattr("core.services.project_creator.save_project_metadata", _fail_save)

    with pytest.raises(RapidKitError):
        pc.create_project(
            kit_name="fastapi.standard",
            project_name="Proj",
            output_dir=tmp_path,
            variables={},
            force=True,
            interactive=False,
            debug=False,
            prompt_func=None,
            print_funcs={
                "info": lambda *_a: None,
                "error": lambda *_a: None,
                "success": lambda *_a: None,
            },
            install_essential_modules=False,
        )


def test_create_project_programmatic_install_flag_affects_generator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When create_project is called programmatically with install_essential_modules=False,
    variables passed to the generator should reflect that choice unless explicitly set by caller."""

    pc = ProjectCreatorService()

    monkeypatch.setattr(pc.registry, "list_kits_names", lambda: ["fastapi.standard"])

    class _DummyKit:
        variables: list[Any] = []
        min_rapidkit_version = "0.0.1"
        display_name = "Demo Kit"
        description = "desc"

    monkeypatch.setattr(pc.registry, "get_kit", lambda *_a, **_k: _DummyKit())

    captured = {}

    class _DummyGenerator:
        def generate(self, output_path: Path, variables: dict[str, Any]) -> list[str]:
            # capture the variables passed for assertions
            captured.update(variables)
            return []

    monkeypatch.setattr(pc.registry, "get_generator", lambda *_a, **_k: _DummyGenerator())

    pc.create_project(
        kit_name="fastapi.standard",
        project_name="Proj",
        output_dir=tmp_path,
        variables={},
        force=True,
        interactive=False,
        debug=False,
        prompt_func=None,
        print_funcs={
            "info": lambda *_a: None,
            "error": lambda *_a: None,
            "success": lambda *_a: None,
        },
        install_essential_modules=False,
    )

    assert captured.get("install_settings") is False
    assert captured.get("install_logging") is False
    assert captured.get("install_deployment") is False


def test_create_project_programmatic_respects_explicit_variables(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pc = ProjectCreatorService()
    monkeypatch.setattr(pc.registry, "list_kits_names", lambda: ["fastapi.standard"])

    class _DummyKit:
        variables: list[Any] = []
        min_rapidkit_version = "0.0.1"
        display_name = "Demo Kit"
        description = "desc"

    monkeypatch.setattr(pc.registry, "get_kit", lambda *_a, **_k: _DummyKit())

    captured = {}

    class _DummyGenerator:
        def generate(self, output_path: Path, variables: dict[str, Any]) -> list[str]:
            captured.update(variables)
            return []

    monkeypatch.setattr(pc.registry, "get_generator", lambda *_a, **_k: _DummyGenerator())

    pc.create_project(
        kit_name="fastapi.standard",
        project_name="Proj",
        output_dir=tmp_path,
        variables={"install_settings": True},
        force=True,
        interactive=False,
        debug=False,
        prompt_func=None,
        print_funcs={
            "info": lambda *_a: None,
            "error": lambda *_a: None,
            "success": lambda *_a: None,
        },
        install_essential_modules=False,
    )

    # Explicit value provided should be preserved
    assert captured.get("install_settings") is True
