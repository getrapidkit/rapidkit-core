import importlib
import sys

import pytest

MODULE_PATH = "runtime.core.logging"


@pytest.fixture()
def logging_module(tmp_path, monkeypatch):
    missing_root = tmp_path / "missing_vendor"
    # Ensure module reloads with controlled environment
    monkeypatch.setenv("RAPIDKIT_VENDOR_ROOT", str(missing_root))
    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    try:
        yield module
    finally:
        module.refresh_vendor_module()
        sys.modules.pop(MODULE_PATH, None)


def test_get_logger_uses_fallback(logging_module):
    logger = logging_module.get_logger("unit-test")
    assert logger.name == "unit-test"
    # Fallback disables propagation to avoid duplicate handlers
    assert logger.propagate is False


def test_get_logging_metadata_reports_exports(logging_module):
    metadata = logging_module.get_logging_metadata()
    assert metadata["module"] == "logging"
    assert metadata["version"] == "1.0.0"
    assert "get_logger" in metadata["available"]


def test_refresh_vendor_module_clears_cache(logging_module, monkeypatch):
    sentinel = object()
    monkeypatch.setattr(logging_module, "_FALLBACK_MODULE", sentinel, raising=False)
    logging_module.refresh_vendor_module()
    assert logging_module._FALLBACK_MODULE is None
    # Cache clear ensures exports still resolve afterwards
    fresh_logger = logging_module.get_logger("fresh")
    assert fresh_logger.name == "fresh"
