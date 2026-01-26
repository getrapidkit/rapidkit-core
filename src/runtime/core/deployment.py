"""FastAPI integration helpers for the deployment module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(slots=True)
class DeploymentAsset:
    name: str
    path: str
    runtime: str


@dataclass(slots=True)
class DeploymentPlan:
    module: str
    version: str
    assets: List[DeploymentAsset]


def _default_assets() -> List[DeploymentAsset]:
    return [
        DeploymentAsset(name="fastapi", path="deployment/fastapi", runtime="python"),
        DeploymentAsset(name="nestjs", path="deployment/nestjs", runtime="node"),
    ]


def build_plan() -> DeploymentPlan:
    return DeploymentPlan(
        module="deployment",
        version="0.2.5",
        assets=_default_assets(),
    )


def describe_plan() -> Dict[str, object]:
    plan = build_plan()
    return {
        "module": plan.module,
        "version": plan.version,
        "assets": [
            {"name": asset.name, "path": asset.path, "runtime": asset.runtime}
            for asset in plan.assets
        ],
    }
