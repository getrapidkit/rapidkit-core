"""Utilities for syncing module vendor payloads into generated kit projects."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from modules.free.essentials.settings.generate import (
    build_base_context as _build_settings_context,
    generate_vendor_files as _generate_settings_vendor_files,
    load_module_config as _load_settings_config,
)
from modules.shared.generator import TemplateRenderer

_SRC_ROOT = Path(__file__).resolve().parents[2]
_SETTINGS_MODULE_ROOT = _SRC_ROOT / "modules" / "free" / "core" / "settings"
_TEMPLATE_RENDERER = TemplateRenderer(_SETTINGS_MODULE_ROOT)


@dataclass(frozen=True)
class _SettingsState:
    config: Dict[str, Any]
    context: Dict[str, Any]
    vendor_root: str
    module_name: str
    version: str


@lru_cache(maxsize=1)
def _load_settings_state() -> _SettingsState:
    config = dict(_load_settings_config())
    context = dict(_build_settings_context(config))
    vendor_root = str(context.get("rapidkit_vendor_root", ".rapidkit/vendor"))
    module_name = str(context.get("rapidkit_vendor_module", config.get("name", "settings")))
    version = str(context.get("rapidkit_vendor_version", config.get("version", "0.0.0")))

    context.setdefault("rapidkit_vendor_root", vendor_root)
    context.setdefault("rapidkit_vendor_module", module_name)
    context.setdefault("rapidkit_vendor_version", version)

    return _SettingsState(
        config=config,
        context=context,
        vendor_root=vendor_root,
        module_name=module_name,
        version=version,
    )


def get_settings_vendor_metadata() -> Dict[str, str]:
    """Return static metadata about the settings module vendor payload."""

    state = _load_settings_state()
    return {
        "vendor_root": state.vendor_root,
        "module_name": state.module_name,
        "version": state.version,
    }


def ensure_settings_vendor_snapshot(project_root: Path | str, *, framework: str = "nestjs") -> Path:
    """Ensure the settings module vendor payload exists inside *project_root*."""

    target_dir = Path(project_root).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        state = _load_settings_state()
        config = state.config
        context = dict(state.context)
        framework_normalized = framework.lower().strip() or "nestjs"
        context.setdefault("framework", framework_normalized)
        context.setdefault("target_framework", framework_normalized)
        context.setdefault("variant", framework_normalized)

        _generate_settings_vendor_files(config, target_dir, _TEMPLATE_RENDERER, context)

        vendor_root = state.vendor_root
        module_name = state.module_name
        version = state.version

        return target_dir / vendor_root / module_name / version
    except Exception as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Failed to sync settings vendor snapshot") from exc


__all__ = ["ensure_settings_vendor_snapshot", "get_settings_vendor_metadata"]
