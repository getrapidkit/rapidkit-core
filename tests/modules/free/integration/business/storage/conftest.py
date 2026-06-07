"""Integration test fixtures."""

import pytest


@pytest.fixture
def fastapi_app():
    """Create FastAPI test app."""
    from fastapi import FastAPI

    app = FastAPI()
    return app


@pytest.fixture
def module_config():
    """Get module configuration."""
    return {
        "adapter": "local",
        "base_path": "./test_storage",
    }
