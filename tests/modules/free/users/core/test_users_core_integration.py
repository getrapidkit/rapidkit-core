from __future__ import annotations

from importlib import import_module
from pathlib import Path

MODULE_ROOT = Path(import_module("modules.free.users.users_core").__file__).resolve().parent


def test_free_users_users_core_integration_smoke() -> None:
    assert MODULE_ROOT.exists()
