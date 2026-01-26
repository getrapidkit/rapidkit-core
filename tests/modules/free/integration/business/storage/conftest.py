"""Integration test fixtures."""

import pytest


@pytest.fixture
def fastapi_app():
    """Create FastAPI test app."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    return TestClient(app)


@pytest.fixture
def module_config():
    """Get module configuration."""
    return {
        "adapter": "local",
        "base_path": "./test_storage",
    }
