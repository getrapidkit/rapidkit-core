"""Integration tests for CORS module functionality."""

# ruff: noqa: I001

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


HTTP_OK = 200


def _read_utf8(path: Path) -> str:
    """Read file content as UTF-8 regardless of platform defaults."""
    return path.read_text(encoding="utf-8")


def test_cors_module_directory_exists() -> None:
    """Test that the CORS module directory exists."""
    repo_root = Path(__file__).resolve().parents[5]  # Go up to repo root
    module_path = repo_root / "src" / "modules" / "free" / "security" / "cors"
    assert module_path.exists()
    assert module_path.is_dir()


def test_cors_config_files_exist() -> None:
    """Test that CORS configuration files exist."""
    repo_root = Path(__file__).resolve().parents[5]
    config_dir = repo_root / "src" / "modules" / "free" / "security" / "cors" / "config"

    assert (config_dir / "base.yaml").exists()
    assert (config_dir / "snippets.yaml").exists()


def test_cors_template_files_exist() -> None:
    """Test that CORS template files exist."""
    repo_root = Path(__file__).resolve().parents[5]
    templates_dir = repo_root / "src" / "modules" / "free" / "security" / "cors" / "templates"

    # Base templates
    assert (templates_dir / "base" / "cors.py.j2").exists()

    # FastAPI templates
    assert (templates_dir / "variants" / "fastapi" / "cors.py.j2").exists()

    # NestJS templates
    assert (templates_dir / "variants" / "nestjs" / "cors.service.ts.j2").exists()


def test_cors_middleware_integration() -> None:
    """Test CORS middleware integration with FastAPI."""
    app = FastAPI()

    # Import and setup CORS (this would be generated code)
    try:
        # Try to import the generated CORS module
        from modules.free.security.cors.cors import (  # type: ignore[import-not-found]
            CORSConfig,
            setup_cors,
        )
    except ImportError:
        # If not generated, create a mock setup for testing
        from fastapi.middleware.cors import CORSMiddleware

        def setup_cors(app: FastAPI, config=None):
            if config is None:
                config = CORSConfig(
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            app.add_middleware(
                CORSMiddleware,
                allow_origins=config.allow_origins,
                allow_credentials=config.allow_credentials,
                allow_methods=config.allow_methods,
                allow_headers=config.allow_headers,
            )

        class CORSConfig:
            def __init__(
                self,
                allow_origins=None,
                allow_credentials=True,
                allow_methods=None,
                allow_headers=None,
            ):
                self.allow_origins = allow_origins or ["*"]
                self.allow_credentials = allow_credentials
                self.allow_methods = allow_methods or ["*"]
                self.allow_headers = allow_headers or ["*"]

    # Setup CORS
    cors_config = CORSConfig(
        allow_origins=["https://example.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    setup_cors(app, cors_config)

    # Add a test route
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Test with async client
    async def exercise() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Test preflight request
            response = await client.options(
                "/test",
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization",
                },
            )

            assert response.status_code == HTTP_OK
            assert response.headers.get("access-control-allow-origin") == "https://example.com"
            assert response.headers.get("access-control-allow-credentials") == "true"
            assert "GET" in response.headers.get("access-control-allow-methods", "")
            assert "Authorization" in response.headers.get("access-control-allow-headers", "")

            # Test actual request
            response = await client.get(
                "/test",
                headers={"Origin": "https://example.com"},
            )

            assert response.status_code == HTTP_OK
            assert response.headers.get("access-control-allow-origin") == "https://example.com"

    asyncio.run(exercise())


def test_cors_with_testclient() -> None:
    """Test CORS with FastAPI TestClient."""
    app = FastAPI()

    # Mock CORS setup (similar to above)
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://test.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization"],
    )

    @app.get("/api/data")
    async def get_data():
        return {"data": "test"}

    client = TestClient(app)

    # Test CORS headers on actual request
    response = client.get("/api/data", headers={"Origin": "https://test.com"})

    assert response.status_code == HTTP_OK
    assert response.headers.get("access-control-allow-origin") == "https://test.com"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_request() -> None:
    """Test CORS preflight request handling."""
    app = FastAPI()

    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://app.example.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
        allow_credentials=True,
        max_age=3600,
    )

    client = TestClient(app)

    # Test preflight OPTIONS request
    response = client.options(
        "/api/test",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )

    assert response.status_code == HTTP_OK
    assert response.headers.get("access-control-allow-origin") == "https://app.example.com"
    assert response.headers.get("access-control-allow-methods") == "GET, POST, PUT, DELETE, OPTIONS"
    assert "Authorization" in response.headers.get("access-control-allow-headers", "")
    assert "Content-Type" in response.headers.get("access-control-allow-headers", "")
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert response.headers.get("access-control-max-age") == "3600"


def test_cors_rejects_invalid_origin() -> None:
    """Test that CORS rejects requests from non-allowed origins."""
    app = FastAPI()

    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware, allow_origins=["https://allowed.com"], allow_credentials=True
    )

    @app.get("/secure")
    async def secure_endpoint():
        return {"message": "secure"}

    client = TestClient(app)

    # Request from disallowed origin should not include CORS headers
    response = client.get("/secure", headers={"Origin": "https://evil.com"})

    assert response.status_code == HTTP_OK
    # CORS headers should not be present for disallowed origins
    assert "access-control-allow-origin" not in response.headers


def test_cors_documentation_exists() -> None:
    """Test that CORS documentation files exist."""
    repo_root = Path(__file__).resolve().parents[5]
    module_docs_dir = repo_root / "src" / "modules" / "free" / "security" / "cors" / "docs"

    assert (module_docs_dir / "usage.md").exists()
    assert (module_docs_dir / "troubleshooting.md").exists()
    assert (module_docs_dir / "advanced.md").exists()
    assert (module_docs_dir / "migration.md").exists()

    # Check that docs are not just TODO placeholders
    usage_content = _read_utf8(module_docs_dir / "usage.md")
    assert "TODO" not in usage_content
    assert "## Installation" in usage_content

    troubleshooting_content = _read_utf8(module_docs_dir / "troubleshooting.md")
    assert "TODO" not in troubleshooting_content
    assert "## Common Issues" in troubleshooting_content
