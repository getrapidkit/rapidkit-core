"""Override contracts and environment-driven toggles for deployment generation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from core.services.override_contracts import ConfigurableOverrideMixin

TRUTHY_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class OverrideState:
    include_ci: bool | None = None
    include_postgres: bool | None = None
    forced_runtime: str | None = None
    extra_workflow_template: Path | None = None
    extra_workflow_root: Path | None = None


def _get_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _is_truthy(value: str | None) -> bool:
    return value is not None and value.lower() in TRUTHY_VALUES


def resolve_override_state(module_root: Path) -> OverrideState:
    include_ci: bool | None = None
    if _is_truthy(_get_env("RAPIDKIT_DEPLOYMENT_SKIP_CI")):
        include_ci = False

    include_postgres: bool | None = None
    if _is_truthy(_get_env("RAPIDKIT_DEPLOYMENT_INCLUDE_POSTGRES")):
        include_postgres = True

    forced_runtime_env = _get_env("RAPIDKIT_DEPLOYMENT_FORCE_RUNTIME")
    forced_runtime = None
    if forced_runtime_env:
        lowered = forced_runtime_env.lower()
        if lowered in {"python", "node"}:
            forced_runtime = lowered

    extra_template_env = _get_env("RAPIDKIT_DEPLOYMENT_EXTRA_WORKFLOW")
    extra_template: Path | None = None
    extra_root: Path | None = None
    if extra_template_env:
        candidate = Path(extra_template_env)
        if not candidate.is_absolute():
            candidate = module_root / candidate
        extra_template = candidate
        extra_root = candidate.parent

    return OverrideState(
        include_ci=include_ci,
        include_postgres=include_postgres,
        forced_runtime=forced_runtime,
        extra_workflow_template=extra_template,
        extra_workflow_root=extra_root,
    )


def apply_base_context_overrides(
    context: Mapping[str, Any],
    state: OverrideState,
) -> dict[str, Any]:
    mutated = dict(context)
    if state.include_ci is not None:
        mutated["include_ci"] = state.include_ci
    if state.include_postgres is not None:
        mutated["include_postgres"] = state.include_postgres
    return mutated


def apply_variant_context_overrides(
    context: Mapping[str, Any],
    state: OverrideState,
) -> dict[str, Any]:
    mutated = dict(context)
    if state.include_ci is not None:
        mutated["include_ci"] = state.include_ci
    if state.include_postgres is not None:
        mutated["include_postgres"] = state.include_postgres
    if state.forced_runtime:
        mutated["runtime"] = state.forced_runtime
    return mutated


class DeploymentOverrides(ConfigurableOverrideMixin):
    """Extend or customise generated behaviour for Deployment."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state(self.module_root)
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return apply_base_context_overrides(context, self.state)

    def apply_variant_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return apply_variant_context_overrides(context, self.state)

    def extra_workflow_template(self) -> Path | None:
        return self.state.extra_workflow_template

    def extra_workflow_root(self) -> Path | None:
        return self.state.extra_workflow_root


__all__ = [
    "DeploymentOverrides",
    "OverrideState",
    "apply_base_context_overrides",
    "apply_variant_context_overrides",
    "resolve_override_state",
]
