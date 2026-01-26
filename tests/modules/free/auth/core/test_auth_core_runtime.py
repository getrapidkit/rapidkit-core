import importlib.util
import sys
from pathlib import Path

import pytest

from modules.free.auth.core.generate import AuthCoreModuleGenerator

RUNTIME_PWD = "SuperSecret123!"
WEAK_PASSWORD = "short"
SUBJECT = "user-123"
AUDIENCE = "web"
SCOPES = ["auth:read"]
PEPPER_VALUE = "static-pepper"


@pytest.fixture(scope="module")
def generator() -> AuthCoreModuleGenerator:
    return AuthCoreModuleGenerator()


@pytest.fixture()
def rendered_fastapi(generator: AuthCoreModuleGenerator, tmp_path: Path) -> Path:
    config = generator.load_module_config()
    base_context = generator.apply_base_context_overrides(generator.build_base_context(config))
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, base_context)
    generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    vendor_root = tmp_path / ".rapidkit" / "vendor" / config["name"] / config["version"]
    runtime_path = vendor_root / base_context["rapidkit_vendor_python_relative"]
    return runtime_path


@pytest.fixture()
def runtime_module(rendered_fastapi: Path) -> object:
    spec = importlib.util.spec_from_file_location("auth_core_vendor", rendered_fastapi)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Failed to load Auth Core runtime")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_hash_roundtrip(runtime_module: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER", PEPPER_VALUE)
    settings = runtime_module.load_settings()
    runtime = runtime_module.AuthCoreRuntime(settings)

    encoded = runtime.hash_password(RUNTIME_PWD)
    assert encoded.startswith("pbkdf2$"), "Encoded hash should use pbkdf2 scheme"
    assert runtime.verify_password(RUNTIME_PWD, encoded) is True
    assert runtime.verify_password("wrong", encoded) is False


def test_password_policy_enforced(runtime_module: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER", PEPPER_VALUE)
    settings = runtime_module.load_settings()
    runtime = runtime_module.AuthCoreRuntime(settings)

    with pytest.raises(ValueError):
        runtime.hash_password(WEAK_PASSWORD)


def test_token_issue_and_verify(runtime_module: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER", PEPPER_VALUE)
    settings = runtime_module.load_settings()
    runtime = runtime_module.AuthCoreRuntime(settings)

    token = runtime.issue_token(SUBJECT, audience=AUDIENCE, scopes=SCOPES)
    payload = runtime.verify_token(token)

    assert payload["sub"] == SUBJECT
    assert payload["iss"] == settings.issuer
    assert payload["aud"] == AUDIENCE
    assert payload["scopes"] == SCOPES


def test_token_expiry(runtime_module: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER", PEPPER_VALUE)
    settings = runtime_module.load_settings({"token_ttl_seconds": 1})
    runtime = runtime_module.AuthCoreRuntime(settings)

    base_time = 1_000_000
    monkeypatch.setattr(runtime_module.time, "time", lambda: base_time)
    token = runtime.issue_token(SUBJECT)

    monkeypatch.setattr(runtime_module.time, "time", lambda: base_time + 5)
    with pytest.raises(ValueError):
        runtime.verify_token(token)


def test_metadata_reports_pepper(runtime_module: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER", PEPPER_VALUE)
    settings = runtime_module.load_settings()
    runtime = runtime_module.AuthCoreRuntime(settings)

    metadata = runtime.metadata()
    assert metadata["pepper_configured"] is True
    assert metadata["issuer"] == settings.issuer
    assert metadata["module"] == "auth_core"
