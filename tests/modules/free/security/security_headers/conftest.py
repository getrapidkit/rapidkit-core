"""Shared pytest fixtures for Security Headers module tests."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator, Mapping, Tuple

import pytest

MODULE_IMPORT_PATH = "modules.free.security.security_headers"


@pytest.fixture(scope="session")
def module_generate() -> ModuleType:
    return importlib.import_module(f"{MODULE_IMPORT_PATH}.generate")


@pytest.fixture(scope="session")
def module_root(module_generate: ModuleType) -> Path:
    return Path(module_generate.__file__).resolve().parent


@pytest.fixture(scope="session")
def module_config(module_generate: ModuleType) -> dict[str, object]:
    return dict(module_generate.load_module_config())


@pytest.fixture(scope="session")
def module_docs(module_config: dict[str, object]) -> dict[str, object]:
    documentation = module_config.get("documentation", {})
    if isinstance(documentation, dict):
        return dict(documentation)
    return {}


def prepare_vendor_package(vendor_root: Path, context: Mapping[str, Any]) -> Path:
    version_dir = (
        vendor_root / context["rapidkit_vendor_module"] / context["rapidkit_vendor_version"]
    )
    security_dir = version_dir / "src/modules/free/security/security_headers"
    health_dir = version_dir / "src/health"
    types_dir = security_dir / "types"

    security_dir.mkdir(parents=True, exist_ok=True)
    health_dir.mkdir(parents=True, exist_ok=True)
    for destination, source in [
        (security_dir / "security_headers_health.py", health_dir / "security_headers.py"),
        (security_dir / "security_headers_types.py", types_dir / "security_headers.py"),
        (health_dir / "security_headers_types.py", types_dir / "security_headers.py"),
    ]:
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return version_dir


def load_module_from_path(module_path: Path, dotted_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        dotted_name,
        module_path,
        submodule_search_locations=[str(module_path.parent)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def fastapi_adapter(
    tmp_path: Path,
    module_generate: ModuleType,
    module_config: Mapping[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Tuple[Any, Any]]:
    renderer = module_generate.TemplateRenderer()
    context = module_generate.build_base_context(module_config)
    module_generate.generate_vendor_files(module_config, tmp_path, renderer, context)
    module_generate.generate_variant_files(module_config, "fastapi", tmp_path, renderer, context)

    vendor_root = tmp_path / ".rapidkit" / "vendor"
    monkeypatch.setenv("RAPIDKIT_VENDOR_ROOT", str(vendor_root))

    prepare_vendor_package(vendor_root, context)

    runtime_path = tmp_path / "src/modules/free/security/security_headers/security_headers.py"
    routes_path = (
        tmp_path / "src/modules/free/security/security_headers/routers/security_headers.py"
    )
    src_root = tmp_path / "src"
    sys_path_entry = str(src_root)
    sys.path.insert(0, sys_path_entry)

    # Ensure package in modules/free/security/security_headers and its parents
    pkg_inits = [
        runtime_path.parents[4] / "__init__.py",  # src/__init__.py
        runtime_path.parents[3] / "__init__.py",  # src/modules/__init__.py
        runtime_path.parents[2] / "__init__.py",  # src/modules/free/__init__.py
        runtime_path.parents[1] / "__init__.py",  # src/modules/free/security/__init__.py
        runtime_path.parent
        / "__init__.py",  # src/modules/free/security/security_headers/__init__.py
        routes_path.parent / "__init__.py",  # routers package
    ]
    for pkg_init in pkg_inits:
        pkg_init.parent.mkdir(parents=True, exist_ok=True)
        pkg_init.write_text("", encoding="utf-8")

    routes_mirror_path = runtime_path.parent / "security_headers_routes.py"
    routes_mirror_path.write_text(
        """
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status


def _runtime_dependency():
    from modules.free.security.security_headers.security_headers import get_runtime

    return get_runtime()


def build_router() -> APIRouter:
    router = APIRouter(prefix="/security-headers", tags=["Security Headers"])

    @router.get(
        "/health",
        summary="Security Headers health check",
        status_code=status.HTTP_200_OK,
    )
    async def read_health(runtime = Depends(_runtime_dependency)):
        return runtime.health_check()

    @router.get(
        "/headers",
        summary="Preview resolved security headers",
        status_code=status.HTTP_200_OK,
    )
    async def list_headers(runtime = Depends(_runtime_dependency)):
        return runtime.headers()

    @router.get(
        "/metadata",
        summary="Module metadata",
        status_code=status.HTTP_200_OK,
    )
    async def read_metadata(runtime = Depends(_runtime_dependency)):
        return runtime.metadata()

    @router.post(
        "/apply",
        summary="Apply security headers to the current response",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def apply_headers(
        response: Response,
        runtime = Depends(_runtime_dependency),
    ) -> Response:
        runtime.apply(response.headers)
        return response

    return router
"""
    )

    runtime_rewrite_target = (
        "spec = importlib.util.spec_from_file_location(module_name, vendor_path)"
    )
    runtime_replacement = (
        "spec = importlib.util.spec_from_file_location("
        "module_name, vendor_path, submodule_search_locations=[str(vendor_path.parent)]"
        ")"
    )
    content = runtime_path.read_text(encoding="utf-8")
    if "import sys" not in content:
        content = content.replace("import os\n", "import os\nimport sys\n")
    if runtime_rewrite_target in content:
        content = content.replace(runtime_rewrite_target, runtime_replacement)
    module_line = "module = importlib.util.module_from_spec(spec)"
    if module_line in content and "sys.modules[module_name] = module" not in content:
        content = content.replace(
            module_line,
            module_line + "\n    sys.modules[module_name] = module",
        )
    runtime_path.write_text(content, encoding="utf-8")

    runtime_module = load_module_from_path(runtime_path, "tests_security.security_headers_runtime")
    sys.modules["modules.free.security.security_headers.security_headers"] = runtime_module
    sys.modules["modules.free.security.security_headers"] = runtime_module
    routes_module = load_module_from_path(
        routes_mirror_path, "tests_security.security_headers_routes"
    )

    yield runtime_module, routes_module

    runtime_module._load_vendor_module.cache_clear()
    sys.path.remove(sys_path_entry)
    for name in [
        "tests_security.security_headers_runtime",
        "tests_security.security_headers_routes",
        "modules.free.security.security_headers.security_headers",
        "modules.free.security.security_headers",
    ]:
        sys.modules.pop(name, None)
