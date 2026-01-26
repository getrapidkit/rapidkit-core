from types import SimpleNamespace
from typing import Iterable, Iterator, List

from cli.commands.create import create_project


class DummyRegistry:
    def __init__(self, kits: Iterable[SimpleNamespace]):
        self._kits = list(kits)

    def list_kits(self) -> List[SimpleNamespace]:
        return self._kits

    def list_kits_names(self) -> List[str]:
        return [kit.name for kit in self._kits]


class DummyService:
    def __init__(self, kits: Iterable[SimpleNamespace], recorder: dict[str, object]):
        self.registry = DummyRegistry(kits)
        self._recorder = recorder

    def create_project(
        self,
        *,
        kit_name: str,
        project_name: str,
        output_dir,
        variables,
        force,
        interactive,
        debug,
        prompt_func,
        print_funcs,
        install_essential_modules,
    ):
        _ = (output_dir, interactive, debug, prompt_func, print_funcs)
        self._recorder["kit_name"] = kit_name
        self._recorder["project_name"] = project_name
        self._recorder["force"] = force
        self._recorder["variables"] = variables
        self._recorder["install_essential_modules"] = install_essential_modules
        return []


def _patch_service(
    monkeypatch, recorder: dict[str, object], kits: Iterable[SimpleNamespace]
) -> None:
    def _factory():  # type: ignore[override]
        return DummyService(kits, recorder)

    monkeypatch.setattr("cli.commands.create.ProjectCreatorService", _factory)


def _patch_prompts(monkeypatch, responses: Iterable[str]) -> None:
    iterator: Iterator[str] = iter(responses)

    def _prompt(_: str) -> str:
        try:
            return next(iterator)
        except StopIteration as err:  # pragma: no cover - indicates test bug
            raise AssertionError("Prompt called more times than expected") from err

    monkeypatch.setattr("cli.commands.create.typer.prompt", _prompt)


def _patch_confirm(monkeypatch, response: bool) -> None:
    monkeypatch.setattr("cli.commands.create.typer.confirm", lambda *_args, **_kwargs: response)


def _patch_confirm_raise(monkeypatch) -> None:
    def _raise(*_args, **_kwargs):
        raise AssertionError("typer.confirm should not be called")

    monkeypatch.setattr("cli.commands.create.typer.confirm", _raise)


def test_interactive_mode_prompts_for_kit(monkeypatch):
    recorder: dict[str, object] = {}
    kits = [SimpleNamespace(name="fastapi.standard", display_name="FastAPI Standard")]
    _patch_service(monkeypatch, recorder, kits)
    _patch_prompts(monkeypatch, ["1", "MyApp"])
    _patch_confirm(monkeypatch, True)

    create_project(kit_name=None, project_name=None)

    assert recorder["kit_name"] == "fastapi.standard"
    assert recorder["project_name"] == "MyApp"
    assert recorder["install_essential_modules"] is True


def test_missing_project_name_prompts_only_for_name(monkeypatch):
    recorder: dict[str, object] = {}
    kits = [SimpleNamespace(name="fastapi.standard", display_name="FastAPI Standard")]
    _patch_service(monkeypatch, recorder, kits)
    _patch_prompts(monkeypatch, ["DemoProj"])
    _patch_confirm(monkeypatch, True)

    create_project(kit_name="fastapi.standard", project_name=None)

    assert recorder["kit_name"] == "fastapi.standard"
    assert recorder["project_name"] == "DemoProj"
    assert recorder["install_essential_modules"] is True


def test_user_can_skip_essential_modules(monkeypatch):
    recorder: dict[str, object] = {}
    kits = [SimpleNamespace(name="fastapi.standard", display_name="FastAPI Standard")]
    _patch_service(monkeypatch, recorder, kits)
    _patch_prompts(monkeypatch, ["1", "MyApp"])
    _patch_confirm(monkeypatch, False)

    create_project(kit_name=None, project_name=None)

    assert recorder["install_essential_modules"] is False


def test_non_interactive_defaults_without_prompt(monkeypatch):
    recorder: dict[str, object] = {}
    kits = [SimpleNamespace(name="fastapi.standard", display_name="FastAPI Standard")]
    _patch_service(monkeypatch, recorder, kits)
    _patch_confirm_raise(monkeypatch)

    create_project(kit_name="fastapi.standard", project_name="DemoApp", install_essentials=None)

    assert recorder["install_essential_modules"] is True
