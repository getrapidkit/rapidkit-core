import json
import os
from pathlib import Path

import pytest

from modules.free.communication.email.frameworks.nestjs import NestJSPlugin
from modules.free.communication.email.overrides import EmailOverrides, resolve_override_state


def test_nestjs_plugin_injects_dependencies(tmp_path: Path) -> None:
    package_path = tmp_path / "package.json"
    package_path.write_text(
        json.dumps({"name": "email", "dependencies": {}, "devDependencies": {}})
    )

    plugin = NestJSPlugin()
    plugin._ensure_package_dependencies(package_path)

    updated = json.loads(package_path.read_text())
    assert updated["dependencies"]["nodemailer"].startswith("^")
    assert updated["devDependencies"]["@types/nodemailer"].startswith("^")


def test_nestjs_plugin_locates_package_in_parent(tmp_path: Path) -> None:
    package_path = tmp_path / "package.json"
    package_path.write_text("{}", encoding="utf-8")

    nested = tmp_path / "src" / "email"
    nested.mkdir(parents=True)

    plugin = NestJSPlugin()
    located = plugin._locate_package_json(nested)
    assert located == package_path


def test_email_overrides_apply_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env = {
        "RAPIDKIT_EMAIL_ENABLED": "1",
        "RAPIDKIT_EMAIL_PROVIDER": "console",
        "RAPIDKIT_EMAIL_FROM_ADDRESS": "notify@example.com",
        "RAPIDKIT_EMAIL_REPLY_TO": "reply@example.com",
        "RAPIDKIT_EMAIL_SMTP_PORT": "2525",
        "RAPIDKIT_EMAIL_SMTP_USE_TLS": "true",
        "RAPIDKIT_EMAIL_TEMPLATE_DIRECTORY": str(tmp_path),
        "RAPIDKIT_EMAIL_DRY_RUN": "false",
        "RAPIDKIT_EMAIL_DEFAULT_HEADERS": "X-Test=1,X-Trace=abc",
    }
    monkeypatch.setattr(os, "environ", env)

    overrides = EmailOverrides(module_root=tmp_path)
    base = {"email_defaults": {}}
    mutated = overrides.apply_base_context(base)

    defaults = mutated["email_defaults"]
    assert defaults["enabled"] is True
    assert defaults["provider"] == "console"
    assert defaults["reply_to"] == "reply@example.com"
    assert defaults["smtp"]["port"] == 2525
    assert defaults["smtp"]["use_tls"] is True
    assert defaults["template"]["directory"] == str(tmp_path)
    assert defaults["default_headers"] == {"X-Test": "1", "X-Trace": "abc"}
    assert mutated["override_metadata"]["email_env_overrides"] is True


def test_email_overrides_post_variant_generation_pins_deps(tmp_path: Path) -> None:
    package_path = tmp_path / "package.json"
    package_path.write_text("{}", encoding="utf-8")

    overrides = EmailOverrides(module_root=tmp_path)
    overrides.post_variant_generation(
        variant_name="nestjs.standard",
        target_dir=tmp_path,
        enriched_context={},
    )

    updated = json.loads(package_path.read_text())
    assert "nodemailer" in updated.get("dependencies", {})
    assert "@types/nodemailer" in updated.get("devDependencies", {})


def test_resolve_override_state_handles_invalid_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDKIT_EMAIL_SMTP_PORT", "not-a-number")
    state = resolve_override_state()
    assert state.smtp_port is None
