from __future__ import annotations

import importlib
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from modules.free.ai.ai_assistant import generate
from modules.shared.generator import TemplateRenderer


def _materialize_runtime(tmp_path: Path) -> Path:
    renderer = TemplateRenderer(generate.MODULE_ROOT / "templates")
    context = generate.build_base_context(generate.load_module_config())

    package_root = tmp_path / f"runtime_{uuid4().hex}"
    ai_pkg = package_root / "ai"
    ai_pkg.mkdir(parents=True)
    (ai_pkg / "__init__.py").write_text("", encoding="utf-8")

    (ai_pkg / "ai_assistant_types.py").write_text(
        renderer.render_template("base/ai_assistant_types.py.j2", context),
        encoding="utf-8",
    )
    (ai_pkg / "ai_assistant.py").write_text(
        renderer.render_template("base/ai_assistant.py.j2", context),
        encoding="utf-8",
    )

    sys.path.insert(0, str(package_root))
    return package_root


def _cleanup_runtime(package_root: Path) -> None:
    for handle in ("ai", "ai.ai_assistant", "ai.ai_assistant_types"):
        sys.modules.pop(handle, None)
    if str(package_root) in sys.path:
        sys.path.remove(str(package_root))


def _load_runtime_module(tmp_path: Path):
    package_root = _materialize_runtime(tmp_path)
    module = importlib.import_module("ai.ai_assistant")
    return module, package_root


def test_validate_config_rejects_duplicate_providers(tmp_path: Path) -> None:
    module, package_root = _load_runtime_module(tmp_path)
    try:
        ProviderConfig = module.ProviderConfig
        Config = module.AiAssistantConfig
        validate_config = module.validate_config
        error = module.AssistantConfigurationError

        config = Config(
            default_provider="echo",
            providers=(
                ProviderConfig(name="echo", provider_type="echo"),
                ProviderConfig(
                    name="echo", provider_type="template", options={"responses": ["hi"]}
                ),
            ),
        )

        with pytest.raises(error) as excinfo:
            validate_config(config)
        assert "unique" in str(excinfo.value)
    finally:
        _cleanup_runtime(package_root)


def test_validate_config_rejects_unknown_default_provider(tmp_path: Path) -> None:
    module, package_root = _load_runtime_module(tmp_path)
    try:
        ProviderConfig = module.ProviderConfig
        Config = module.AiAssistantConfig
        validate_config = module.validate_config
        error = module.AssistantConfigurationError

        config = Config(
            default_provider="ghost",
            providers=(ProviderConfig(name="echo", provider_type="echo"),),
        )

        with pytest.raises(error) as excinfo:
            validate_config(config)
        assert "Default provider" in str(excinfo.value)
    finally:
        _cleanup_runtime(package_root)
