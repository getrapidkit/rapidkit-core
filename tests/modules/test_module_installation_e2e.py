"""End-to-end smoke tests that install RapidKit modules inside throwaway projects."""

from __future__ import annotations

import os
from typing import Dict, Tuple

import pytest

from tests.utils.module_inventory import discover_active_free_module_matrix

DEFAULT_MATRIX = {
    "free/database/db_postgres": ("fastapi/standard", "nestjs/standard"),
}


def _parse_matrix(value: str) -> Dict[str, Tuple[str, ...]]:
    matrix: Dict[str, Tuple[str, ...]] = {}
    if not value:
        return matrix
    for chunk in value.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        name, _, profiles_raw = chunk.partition(":")
        if not name or not profiles_raw:
            continue
        profiles = tuple(part.strip() for part in profiles_raw.split(",") if part.strip())
        if profiles:
            matrix[name.strip()] = profiles
    return matrix


ENV_MATRIX = _parse_matrix(os.getenv("RAPIDKIT_E2E_MATRIX", ""))
AUTO_MATRIX = discover_active_free_module_matrix()
MODULE_MATRIX = ENV_MATRIX or AUTO_MATRIX or DEFAULT_MATRIX


def _parameter_id(module: str, profile: str) -> str:
    slug = module
    if module.startswith("free/"):
        slug = module.split("/", 1)[1]
    return f"{slug}-{profile}"


PARAMETERS = [
    pytest.param(module, profile, id=_parameter_id(module, profile))
    for module, profiles in MODULE_MATRIX.items()
    for profile in profiles
]

if not PARAMETERS:
    pytestmark = pytest.mark.skip(reason="No module profiles resolved for installation smoke test")


@pytest.mark.slow
@pytest.mark.e2e
@pytest.mark.parametrize(
    "module_name,profile",
    PARAMETERS,
)
def test_module_end_to_end_installation(module_name: str, profile: str, rapidkit_simulator):
    result = rapidkit_simulator.install_module(module_name, profile)
    expected_files = rapidkit_simulator.expected_files(module_name, profile)
    missing = [path for path in expected_files if not (result.project_path / path).exists()]
    assert not missing, f"Missing generated files after installation: {missing}"
    assert module_name in result.add_module_output
