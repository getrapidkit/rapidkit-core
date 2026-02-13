"""Utilities for managing generated health check scaffolding."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from string import Template
from textwrap import dedent
from typing import Iterable, List, Sequence, Tuple

_DEFAULT_HEALTH_IMPORTS: Tuple[Tuple[str, str], ...] = (
    ("src.health.logging", "register_logging_health"),
    ("src.health.deployment", "register_deployment_health"),
    ("src.health.middleware", "register_middleware_health"),
    ("src.health.settings", "register_settings_health"),
    ("src.health.redis", "register_redis_health"),
)


@dataclass(frozen=True)
class HealthShimSpec:
    """Describe the vendor-backed shim that needs to be generated."""

    module_name: str
    vendor_module: str
    vendor_version: str
    vendor_relative_path: str
    target_relative_path: str
    # legacy alias path removed — canonical path is `src/health/<module>.py`
    slug: str | None = None


_VENDOR_HEALTH_WRAPPER_TEMPLATE = Template(
    dedent(
        '''
        """Project shim exposing vendor health helpers for $module_name."""

        from __future__ import annotations

        import importlib.util
        import os
        import sys
        from functools import lru_cache
        from pathlib import Path
        from types import ModuleType
        from typing import Any, Optional

        _VENDOR_MODULE = "$vendor_module"
        _VENDOR_VERSION = "$vendor_version"
        _VENDOR_RELATIVE_PATH = "$vendor_relative_path"
        _VENDOR_ROOT_ENV = "RAPIDKIT_VENDOR_ROOT"
        _CACHE_PREFIX = "rapidkit_vendor_$cache_slug"

        DEFAULT_HEALTH_PREFIX = "/api/health/module/$slug"


        def _project_root() -> Path:
            current = Path(__file__).resolve()
            for ancestor in current.parents:
                if (ancestor / ".rapidkit").exists():
                    return ancestor
                if (ancestor / "pyproject.toml").exists() or (ancestor / "package.json").exists():
                    return ancestor
            return current.parents[2]


        def _ensure_proxy_package(name: str, path: Path) -> None:
            if not path.exists():
                return

            original = sys.modules.get(name)
            proxy = ModuleType(name)
            if original is not None:
                proxy.__dict__.update(original.__dict__)
            proxy.__path__ = [str(path)]
            sys.modules[name] = proxy


        def _vendor_module_root() -> Optional[Path]:
            """Locate the vendor module root containing <name>.py + types/ directory."""

            base = _vendor_base_dir() / "src" / "modules"
            if not base.exists():
                return None

            module_name = _VENDOR_MODULE.split("/")[-1]
            for candidate in base.rglob(f"{module_name}.py"):
                if candidate.name != f"{module_name}.py":
                    continue
                if candidate.parent.name != module_name:
                    continue
                return candidate.parent
            return None


        def _ensure_vendor_namespaces() -> None:
            module_root = _vendor_module_root()
            if module_root is not None:
                _ensure_proxy_package("database", module_root)
                _ensure_proxy_package("types", module_root / "types")

            _ensure_proxy_package("health", _vendor_base_dir() / "src" / "health")


        def _vendor_root() -> Path:
            override = os.getenv(_VENDOR_ROOT_ENV)
            if override:
                return Path(override).expanduser().resolve()
            return _project_root() / ".rapidkit" / "vendor"


        def _vendor_base_dir() -> Path:
            root = _vendor_root()
            module_dir = root / _VENDOR_MODULE
            preferred = module_dir / _VENDOR_VERSION if _VENDOR_VERSION else None
            if preferred and preferred.exists():
                return preferred
            candidates = sorted(
                (path for path in module_dir.glob("*") if path.is_dir()), reverse=True
            )
            if candidates:
                return candidates[0]
            raise RuntimeError(
                "RapidKit vendor payload for '{module}' not found under {root}. Re-run `rapidkit modules install {module}`.".format(
                    module=_VENDOR_MODULE,
                    root=root,
                )
            )


        def _vendor_file() -> Path:
            if not _VENDOR_RELATIVE_PATH:
                raise RuntimeError(
                    "Vendor health relative path missing for module '{module}'. Please reinstall the module.".format(
                        module=_VENDOR_MODULE,
                    )
                )
            return _vendor_base_dir() / _VENDOR_RELATIVE_PATH


        @lru_cache(maxsize=1)
        def _load_vendor_module() -> ModuleType:
            vendor_path = _vendor_file()
            if not vendor_path.exists():
                raise RuntimeError(
                    "RapidKit vendor health runtime missing at {path}. Re-run `rapidkit modules install {module}`.".format(
                        path=vendor_path,
                        module=_VENDOR_MODULE,
                    )
                )

            _ensure_vendor_namespaces()

            vendor_base = str(_vendor_base_dir())
            if vendor_base not in sys.path:
                sys.path.insert(0, vendor_base)

            module_name = _CACHE_PREFIX + _VENDOR_MODULE.replace("/", "_") + "_health"
            spec = importlib.util.spec_from_file_location(module_name, vendor_path)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Unable to load vendor health runtime from {vendor_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules.setdefault(module_name, module)
            spec.loader.exec_module(module)
            return module


        def _resolve_export(name: str) -> Any:
            vendor = _load_vendor_module()
            try:
                return getattr(vendor, name)
            except AttributeError as exc:  # pragma: no cover - defensive guard
                raise RuntimeError(
                    "Vendor health module '{module}' missing attribute '{attribute}'".format(
                        module=_VENDOR_RELATIVE_PATH,
                        attribute=name,
                    )
                ) from exc


        def refresh_vendor_module() -> None:
            """Clear import caches after vendor upgrades."""

            _load_vendor_module.cache_clear()


        def build_health_router(prefix: str = DEFAULT_HEALTH_PREFIX) -> Any:
            """Return a FastAPI router sourced from the vendor health runtime."""

            try:
                factory = _resolve_export("build_health_router")
            except RuntimeError:
                factory = None

            if callable(factory):
                try:
                    return factory(prefix=prefix)
                except TypeError:  # pragma: no cover - factory without prefix support
                    return factory()

            try:
                router = _resolve_export("router")
                if router is not None:
                    return router
            except RuntimeError:
                router = None

            try:
                factory = _resolve_export("create_health_router")
            except RuntimeError:
                factory = None

            if callable(factory):
                try:
                    return factory(prefix=prefix)
                except TypeError:  # pragma: no cover - factory without prefix support
                    return factory()

            try:
                from fastapi import APIRouter  # type: ignore
            except ImportError:  # pragma: no cover - FastAPI optional for template rendering
                APIRouter = None  # type: ignore[assignment]

            if APIRouter is not None:
                router = APIRouter(prefix=prefix, tags=["Health", _VENDOR_MODULE])

                @router.get("/health", summary=f"{_VENDOR_MODULE} health check")
                async def read_health() -> dict[str, Any]:
                    return {
                        "module": _VENDOR_MODULE,
                        "status": "unknown",
                        "detail": "runtime not initialized",
                        "warnings": [],
                    }

                return router

            raise RuntimeError(
                "Vendor health runtime for '{module}' does not expose a router. Regenerate the module outputs.".format(
                    module=_VENDOR_MODULE,
                )
            )


        def create_health_router(prefix: str = DEFAULT_HEALTH_PREFIX) -> Any:
            """Compatibility wrapper expected by integration tests."""

            return build_health_router(prefix=prefix)


        def _fallback_register(app: Any) -> None:
            try:
                from fastapi import FastAPI  # type: ignore
            except ImportError:  # pragma: no cover - FastAPI optional for template rendering
                FastAPI = None  # type: ignore[assignment]

            if FastAPI is not None and not isinstance(app, FastAPI):
                raise TypeError(
                    "register_${module_name}_health expects a FastAPI application instance"
                )

            router = build_health_router()
            app.include_router(router)


        try:
            $register_symbol = _resolve_export("$register_symbol")
        except RuntimeError:
            $register_symbol = _fallback_register


        try:
            router = build_health_router()
        except Exception:  # pragma: no cover - allow non-router health runtimes
            router = None


        def __getattr__(item: str) -> Any:
            vendor = _load_vendor_module()
            try:
                return getattr(vendor, item)
            except AttributeError as exc:  # pragma: no cover - propagate helpful error
                raise AttributeError(item) from exc


        __all__ = sorted(
            set(getattr(_load_vendor_module(), "__all__", []))
            | {
                "build_health_router",
                "create_health_router",
                "refresh_vendor_module",
                "$register_symbol",
                "router",
            }
        )
        '''
    ).strip()
)


_HEALTH_ALIAS_TEMPLATE = Template(
    dedent(
        '''
        """Compatibility alias for $module_name health shim."""

        from __future__ import annotations

        from typing import Any

        from src.health import $module_name as _health_module


        def __getattr__(item: str) -> Any:
            return getattr(_health_module, item)


        router = getattr(_health_module, "router", None)
        register_${module_name}_health = getattr(_health_module, "register_${module_name}_health")
        build_health_router = getattr(_health_module, "build_health_router")
        refresh_vendor_module = getattr(_health_module, "refresh_vendor_module")
        DEFAULT_HEALTH_PREFIX = getattr(_health_module, "DEFAULT_HEALTH_PREFIX", "/api/health/module/$slug")

        __all__ = getattr(_health_module, "__all__", [])
        '''
    ).strip()
)


_BUILTIN_HEALTH_MODULES: Tuple[str, ...] = (
    "logging",
    "deployment",
    "middleware",
    "settings",
    "redis",
)

_IMPORT_LINE_PATTERN = re.compile(r"\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")

_DATABASE_INIT_TEMPLATE = dedent(
    '''
"""Database health package exports."""

from __future__ import annotations

__all__: list[str] = []
'''
)


_HEALTH_REGISTRY_TEMPLATE = dedent(
    '''
"""Shared registry for aggregating RapidKit module health routers."""

from __future__ import annotations

import logging
from typing import Any, Callable, Iterable, List

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter
except ImportError:  # pragma: no cover - FastAPI not installed yet
    APIRouter = None  # type: ignore[assignment]

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover - FastAPI not installed yet
    FastAPI = None  # type: ignore[assignment]

try:  # pragma: no cover - defensive import guarding
    from src.health import (
        iter_health_registrars as _core_iter_registrars,
        list_health_routes as _core_list_health_routes,
    )
except ImportError:  # pragma: no cover - registry not generated yet

    def _core_iter_registrars() -> Iterable[Callable[[Any], None]]:
        return ()

    def _core_list_health_routes(prefix: str = "/api/health") -> List[dict[str, Any]]:
        return []


def _collect_registrars() -> List[Callable[[Any], None]]:
    registrars: List[Callable[[Any], None]] = []
    for registrar in _core_iter_registrars():
        if callable(registrar):
            registrars.append(registrar)
    return registrars


def build_health_router(*, title: str = "RapidKit Module Health"):
    """Construct an APIRouter aggregating all registered module health routes."""

    if APIRouter is None or FastAPI is None:
        raise RuntimeError(
            "FastAPI must be installed to use the shared health registry"
        )

    staging_app = FastAPI(title=title)
    for registrar in _collect_registrars():
        try:
            registrar(staging_app)
        except Exception as exc:  # pragma: no cover - defensive guard  # noqa: BLE001
            logger.warning("Health registrar failed; skipping", exc_info=exc)
            continue

    router = APIRouter()
    router.include_router(staging_app.router)
    return router


def list_registered_health_routes(prefix: str = "/api/health") -> List[dict[str, Any]]:
    """Expose metadata for all registered module health endpoints."""

    try:
        return list(_core_list_health_routes(prefix=prefix))
    except Exception as exc:  # pragma: no cover - defensive guard  # noqa: BLE001
        logger.warning("Listing health routes failed", exc_info=exc)
        return []


__all__ = ["build_health_router", "list_registered_health_routes"]
'''
)


def _render_health_init(imports: Sequence[Tuple[str, str]]) -> str:
    indent = " " * 16
    imports_block = "\n".join(
        f'{indent}("{module_path}", "{attribute}"),' for module_path, attribute in imports
    )

    raw_template = '''
            """Health package aggregator for RapidKit generated modules."""

            from __future__ import annotations

            import pkgutil
            from importlib import import_module
            from typing import Any, Callable, Dict, Iterable, List, Set, Tuple

            _FALLBACK_IMPORTS: Tuple[Tuple[str, str], ...] = (
${imports_block}
            )

            DEFAULT_HEALTH_PREFIX = "/api/health"
            DEFAULT_MODULE_SEGMENT = "module"


            def _iter_candidate_imports() -> List[Tuple[str, str]]:
                discovered: List[Tuple[str, str]] = list(_FALLBACK_IMPORTS)
                seen: Set[Tuple[str, str]] = set(discovered)
                package_prefix = f"{__name__}."
                dynamic: List[Tuple[str, str]] = []
                for module_info in pkgutil.walk_packages(__path__, prefix=package_prefix):
                    module_path = module_info.name
                    slug = module_path.rsplit(".", 1)[-1]
                    attribute = f"register_{slug}_health"
                    candidate = (module_path, attribute)
                    if candidate in seen:
                        continue
                    seen.add(candidate)
                    dynamic.append(candidate)
                dynamic.sort(key=lambda item: item[0])
                discovered.extend(dynamic)
                return discovered


            def _resolve_health_modules() -> List[Tuple[str, Callable[[Any], None], str]]:
                resolved: List[Tuple[str, Callable[[Any], None], str]] = []
                for module_path, attribute in _iter_candidate_imports():
                    try:
                        module = import_module(module_path)
                        registrar = getattr(module, attribute)
                    except (ImportError, AttributeError):
                        continue
                    if callable(registrar):
                        slug = module_path.rsplit(".", 1)[-1]
                        resolved.append((module_path, registrar, slug))
                return resolved


            def _discover_registrars() -> List[Callable[[Any], None]]:
                registrars: List[Callable[[Any], None]] = []
                for _module_path, registrar, _slug in _resolve_health_modules():
                    registrars.append(registrar)
                return registrars


            def iter_health_registrars() -> Iterable[Callable[[Any], None]]:
                """Yield available health registrar callables."""

                yield from _discover_registrars()


            def register_health_routes(app: Any) -> None:
                """Register all detected health routers against the provided FastAPI app."""

                for registrar in _discover_registrars():
                    registrar(app)


            def _build_module_path(prefix: str, slug: str) -> str:
                cleaned_prefix = prefix.rstrip("/") or "/"
                cleaned_slug = slug.replace("_", "-")
                return f"{cleaned_prefix}/{DEFAULT_MODULE_SEGMENT}/{cleaned_slug}"


            def list_health_routes(prefix: str = DEFAULT_HEALTH_PREFIX) -> List[Dict[str, str]]:
                """Return metadata about available module health endpoints."""

                routes: List[Dict[str, str]] = []
                for module_path, _registrar, slug in _resolve_health_modules():
                    routes.append(
                        {
                            "module_path": module_path,
                            "slug": slug,
                            "path": _build_module_path(prefix, slug),
                        }
                    )
                return routes


            __all__ = [
                "iter_health_registrars",
                "register_health_routes",
                "list_health_routes",
            ]
            '''

    rendered = Template(raw_template).substitute(imports_block=imports_block)
    normalized = dedent(rendered).strip("\n")
    return f"{normalized}\n"


_HEALTH_INIT_TEMPLATE = _render_health_init(_DEFAULT_HEALTH_IMPORTS)


def _write_file_if_missing(path: Path, *, content: str) -> None:
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError:
            existing = None
        if existing is not None and existing.strip():
            if "list_health_routes" not in existing or "_iter_candidate_imports" not in existing:
                path.write_text(content, encoding="utf-8")
            return
    path.write_text(content, encoding="utf-8")


def ensure_health_package(
    output_dir: Path,
    *,
    include_database: bool = False,
    extra_imports: Sequence[Tuple[str, str]] | None = None,
) -> None:
    """Ensure the health package scaffold exists within the generated project.

    Parameters
    ----------
    output_dir:
        Root directory where the module is being generated.
    include_database:
        When True, create ``src/health/database/__init__.py`` so nested database
        health modules can be imported safely.
    extra_imports:
        Optional additional ``(module_path, attribute)`` pairs to append to the
        generated aggregator's import list. These are merged with the default set.
    """

    # canonical public health package used by generated projects
    health_dir = output_dir / "src/health"
    health_dir.mkdir(parents=True, exist_ok=True)

    init_path = health_dir / "__init__.py"

    existing_contents: str = ""
    if init_path.exists():
        try:
            existing_contents = init_path.read_text(encoding="utf-8")
        except OSError:
            existing_contents = ""

    imports: List[Tuple[str, str]] = list(_DEFAULT_HEALTH_IMPORTS)

    def _extend_unique(source: List[Tuple[str, str]], items: Iterable[Tuple[str, str]]) -> None:
        for module_path, attribute in items:
            candidate = (module_path, attribute)
            if candidate not in source:
                source.append(candidate)

    if existing_contents:
        current_pairs = _IMPORT_LINE_PATTERN.findall(existing_contents)
        _extend_unique(imports, current_pairs)

    if extra_imports:
        _extend_unique(imports, extra_imports)

    desired_template = _render_health_init(imports)
    if existing_contents != desired_template:
        init_path.write_text(desired_template, encoding="utf-8")

    if include_database:
        database_dir = health_dir / "database"
        database_dir.mkdir(parents=True, exist_ok=True)
        _write_file_if_missing(database_dir / "__init__.py", content=_DATABASE_INIT_TEMPLATE)

    _ensure_main_health_registration(output_dir)
    _ensure_health_router_metadata(output_dir)
    _ensure_health_registry_bridge(output_dir)
    # Under canonical-only policy we do not generate or sync legacy
    # compatibility wrappers into src/core/health — generated projects
    # should only expose canonical modules under src/health.
    _ensure_routing_mount_uses_registry(output_dir)


# module exports are defined at end of file after all helpers are declared


def _write_text_if_different(path: Path, *, content: str) -> None:
    try:
        existing = path.read_text(encoding="utf-8")
    except OSError:
        existing = None

    if existing == content:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_vendor_health_wrapper(
    *,
    module_name: str,
    vendor_module: str,
    vendor_version: str,
    vendor_relative_path: str,
    slug: str,
) -> str:
    cache_slug = module_name.replace("/", "_").replace("-", "_")
    register_symbol = f"register_{module_name}_health"
    payload = _VENDOR_HEALTH_WRAPPER_TEMPLATE.substitute(
        module_name=module_name,
        vendor_module=vendor_module,
        vendor_version=vendor_version,
        vendor_relative_path=vendor_relative_path,
        cache_slug=cache_slug,
        slug=slug,
        register_symbol=register_symbol,
    )
    return payload + "\n"


def _render_health_alias(*, module_name: str, slug: str) -> str:
    return _HEALTH_ALIAS_TEMPLATE.substitute(module_name=module_name, slug=slug) + "\n"


def ensure_vendor_health_shim(output_dir: Path, *, spec: HealthShimSpec) -> None:
    """Generate the vendor-backed shim + optional compatibility alias."""

    slug = spec.slug or spec.module_name.replace("_", "-")
    shim_body = _render_vendor_health_wrapper(
        module_name=spec.module_name,
        vendor_module=spec.vendor_module,
        vendor_version=spec.vendor_version,
        vendor_relative_path=spec.vendor_relative_path,
        slug=slug,
    )
    target = output_dir / spec.target_relative_path
    _write_text_if_different(target, content=shim_body)

    # Canonical-only policy: do not generate legacy `src/core/*_health.py` aliases.
    # Old compatibility aliases were removed; projects should use `src/health/<module>.py`.


def _ensure_main_health_registration(project_root: Path) -> None:
    main_path = project_root / "src" / "main.py"
    if not main_path.exists():
        return
    try:
        contents = main_path.read_text(encoding="utf-8")
    except OSError:
        return
    if "_register_health_routes" in contents:
        return

    import_block = "\n".join(
        [
            "try:",
            "    from src.health import register_health_routes as _register_health_routes",
            "except ImportError:  # pragma: no cover - health package not generated yet",
            "    def _register_health_routes(_: FastAPI) -> None:",
            "        return None",
            "else:",
            "    def _register_health_routes(app: FastAPI) -> None:",
            "        try:",
            "            _register_health_routes(app)",
            "        except Exception:  # pragma: no cover - defensive best-effort registration",
            "            return None",
            "",
        ]
    )

    if "# <<<inject:imports>>>" in contents:
        contents = contents.replace(
            "# <<<inject:imports>>>", f"{import_block}\n# <<<inject:imports>>>", 1
        )
    else:
        contents = import_block + contents

    if 'app.include_router(api_router, prefix="/api")' in contents:
        contents = contents.replace(
            'app.include_router(api_router, prefix="/api")',
            'app.include_router(api_router, prefix="/api")\n_register_health_routes(app)',
            1,
        )

    main_path.write_text(contents, encoding="utf-8")


def _ensure_health_registry_bridge(project_root: Path) -> None:
    health_pkg = project_root / "src" / "health"
    health_pkg.mkdir(parents=True, exist_ok=True)

    init_path = health_pkg / "__init__.py"
    if not init_path.exists():
        init_path.write_text(
            '"""RapidKit module health namespace."""\n\n__all__ = []\n',
            encoding="utf-8",
        )

    registry_path = health_pkg / "registry.py"
    desired = _HEALTH_REGISTRY_TEMPLATE.strip() + "\n"
    try:
        existing = registry_path.read_text(encoding="utf-8")
    except OSError:
        existing = ""
    if existing.strip() != desired.strip():
        registry_path.write_text(desired, encoding="utf-8")


def _sync_module_health_wrappers(_project_root: Path) -> None:
    """No-op under canonical-only health layout.

    We intentionally do not create or sync compatibility wrappers under
    `src/core/health` when generating projects. Generated projects should
    only expose canonical module health files under `src/health`.
    """
    return


def _relocate_custom_health_modules(project_root: Path) -> None:
    private_health_root = project_root / "src" / "core" / "health"
    if not private_health_root.exists():
        return

    public_health_root = project_root / "src" / "health"
    public_health_root.mkdir(parents=True, exist_ok=True)

    skip_modules = set(_BUILTIN_HEALTH_MODULES) | {"__init__", "registry"}

    for module_file in sorted(private_health_root.glob("*.py")):
        module_name = module_file.stem
        if module_name in skip_modules or module_name.startswith("_"):
            continue

        destination = public_health_root / module_file.name
        if destination.exists():
            continue

        try:
            contents = module_file.read_text(encoding="utf-8")
        except OSError:
            continue

        if (
            "Adapter registering" in contents
            or "Project shim exposing vendor health helpers" in contents
        ):
            continue

        destination.write_text(contents, encoding="utf-8")
        wrapper_body = _generate_health_wrapper_body(module_name)
        module_file.write_text(wrapper_body, encoding="utf-8")


def _ensure_builtin_health_proxies(project_root: Path) -> None:
    private_health_root = project_root / "src" / "core" / "health"
    if not private_health_root.exists():
        return

    public_health_root = project_root / "src" / "health"
    public_health_root.mkdir(parents=True, exist_ok=True)

    for module_name in _BUILTIN_HEALTH_MODULES:
        source_path = private_health_root / f"{module_name}.py"
        if not source_path.exists():
            continue

        proxy_path = public_health_root / f"{module_name}.py"
        if proxy_path.exists():
            continue

        proxy_body = _generate_public_health_proxy_body(module_name)
        proxy_path.write_text(proxy_body, encoding="utf-8")


def _generate_public_health_proxy_body(module_name: str) -> str:
    return (
        dedent(
            f'''
"""Public proxy exposing {module_name} health helpers from the core namespace."""

from __future__ import annotations

from typing import Any

try:
    from src.health import {module_name} as _core_health_module
except ImportError:  # pragma: no cover - module not generated yet
    _core_health_module = None  # type: ignore[assignment]


router = getattr(_core_health_module, "router", None)
create_health_router = getattr(_core_health_module, "create_health_router", None)
build_health_router = getattr(_core_health_module, "build_health_router", None)


def __getattr__(item: str) -> Any:
    if _core_health_module is None:
        raise AttributeError(
            "{module_name} health module unavailable; regenerate the module outputs.",
        )
    return getattr(_core_health_module, item)


def __dir__() -> list[str]:
    if _core_health_module is None:
        return []
    return sorted(set(dir(_core_health_module)))


__all__ = getattr(_core_health_module, "__all__", [])
'''
        ).strip()
        + "\n"
    )


def synchronize_health_package(project_root: Path) -> None:
    """Reconcile health packages after code generation."""

    _ensure_health_registry_bridge(project_root)
    _relocate_custom_health_modules(project_root)
    # Do not generate legacy compatibility proxies or sync wrappers into
    # `src/core/health` (canonical-only layout). Generated projects must
    # expose module health from `src/health/<module>.py` only.


def _generate_health_wrapper_body(module_name: str) -> str:
    slug = module_name.replace("_", "-")
    return (
        dedent(
            f'''
"""Adapter registering {module_name} health routes with the shared registry."""

from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover - FastAPI unavailable during stub generation
    FastAPI = None  # type: ignore[assignment]

try:
    from src.health import {module_name} as _health_module
except ImportError:  # pragma: no cover - module not generated yet
    _health_module = None  # type: ignore[assignment]

HEALTH_SLUG = "{slug}"


def _resolve_router() -> Any | None:
    if _health_module is None:
        return None

    factory = getattr(_health_module, "create_health_router", None)
    router = None
    if callable(factory):
        try:
            router = factory(prefix="/api/health/module/" + HEALTH_SLUG)
        except TypeError:  # pragma: no cover - factory without prefix support
            router = factory()
    if router is None:
        router = getattr(_health_module, "router", None)
    return router


def register_{module_name}_health(app: Any) -> None:
    """Attach the {module_name} health router to the provided FastAPI app."""

    if FastAPI is not None and not isinstance(app, FastAPI):
        raise TypeError(
            "register_{module_name}_health expects a FastAPI application instance",
        )

    router = _resolve_router()
    if router is None:
        raise RuntimeError(
            "{module_name} health router is unavailable; regenerate the module outputs.",
        )

    app.include_router(router)


__all__ = ["register_{module_name}_health"]
'''
        ).strip()
        + "\n"
    )


def _ensure_routing_mount_uses_registry(project_root: Path) -> None:
    routing_init = project_root / "src" / "routing" / "__init__.py"
    if not routing_init.exists():
        return

    try:
        contents = routing_init.read_text(encoding="utf-8")
    except OSError:
        return

    patterns = (
        'api_router.include_router(health_router, prefix="/health", tags=["health"])',
        "api_router.include_router(health_router, prefix='/health', tags=['health'])",
    )

    updated = contents
    for pattern in patterns:
        if pattern in updated:
            updated = updated.replace(pattern, "api_router.include_router(health_router)")

    if updated != contents:
        routing_init.write_text(updated, encoding="utf-8")


def _ensure_health_router_metadata(project_root: Path) -> None:
    routing_path = project_root / "src" / "routing" / "health.py"
    if not routing_path.exists():
        return
    try:
        contents = routing_path.read_text(encoding="utf-8")
    except OSError:
        return

    if '@router.get("/healths"' in contents:
        contents = contents.replace('@router.get("/healths"', '@router.get("/modules"', 1)

    updated = contents

    if '@router.get("/healths"' in updated:
        updated = updated.replace('@router.get("/healths"', '@router.get("/modules"', 1)

    if "_list_registered_health_routes" not in updated:
        import_snippet = "\n".join(
            [
                "from fastapi import APIRouter",
                "",
                "try:",
                "    from src.health.registry import (",
                "        list_registered_health_routes as _list_registered_health_routes,",
                "    )",
                "except ImportError:  # pragma: no cover - health registry not available yet",
                '    def _list_registered_health_routes(prefix: str = "/api/health") -> list[dict[str, str]]:',
                "        return []",
                "",
            ]
        )
        if "from fastapi import APIRouter" in updated:
            updated = updated.replace("from fastapi import APIRouter", import_snippet, 1)
        else:
            updated = import_snippet + updated

    updated = updated.replace(
        'return {"routes": _list_health_routes()}',
        'return {"routes": _list_registered_health_routes()}',
    )

    router_prefix_replacements = {
        'router = APIRouter(tags=["health"])': 'router = APIRouter(prefix="/health", tags=["health"])',
        "router = APIRouter(tags=['health'])": "router = APIRouter(prefix=\"/health\", tags=['health'])",
    }
    for old, new in router_prefix_replacements.items():
        if old in updated and new not in updated:
            updated = updated.replace(old, new, 1)

    # Ensure the /modules health catalog is present and uses the unified implementation
    # Only remove existing non-canonical /modules handlers if they are present and
    # do not already include the canonical health_catalog implementation.
    if '@router.get("/modules"' in updated and "async def health_catalog" not in updated:
        updated = updated[: updated.find('@router.get("/modules"')]

    if "async def health_catalog" not in updated:
        catalog_snippet = "\n".join(
            [
                "",
                '@router.get("/modules", summary="Registered module health endpoints")',
                "async def health_catalog(request: Request, fetch: bool = False) -> dict[str, Any]:",
                '    """Expose metadata for module-provided health routes.\n\n'
                "    When `fetch=True` this endpoint will attempt to call each registered module\n"
                '    health path internally and return their payloads under `results`."""',
                "",
                "    routes = _list_registered_health_routes()",
                "    if not fetch:",
                '        return {"routes": routes}',
                "",
                "    # Attempt to fetch each module's health path from the running app using httpx",
                "    try:",
                "        import asyncio",
                "        import httpx",
                "    except Exception:  # pragma: no cover - optional runtime dependencies",
                '        return {"routes": routes, "results": [], "warning": "httpx unavailable"}',
                "",
                "    results = []",
                "    async def _fetch(path: str) -> dict[str, Any]:",
                "        try:",
                '            async with httpx.AsyncClient(app=request.app, base_url="http://test") as client:',
                "                resp = await client.get(path)",
                "                try:",
                "                    payload = resp.json()",
                "                except Exception:",
                '                    payload = {"raw_text": (await resp.aread()).decode(errors="replace")}',
                '                return {"path": path, "status_code": resp.status_code, "payload": payload}',
                "        except Exception as exc:  # pragma: no cover - external errors possible",
                '            return {"path": path, "error": str(exc)}',
                "",
                "    tasks = [_fetch(route['path']) for route in routes]",
                "    responses = await asyncio.gather(*tasks, return_exceptions=False)",
                "    results.extend(responses)",
                "",
                '    return {"routes": routes, "results": results}',
                "",
            ]
        )
        # ensure Request and typing imports exist (best-effort)
        if "from fastapi import APIRouter" in updated and "Request" not in updated:
            updated = updated.replace(
                "from fastapi import APIRouter", "from fastapi import APIRouter, Request"
            )
        if "from typing import Any" not in updated:
            if "from fastapi import APIRouter" in updated:
                updated = updated.replace(
                    "from fastapi import APIRouter",
                    "from fastapi import APIRouter\nfrom typing import Any",
                    1,
                )
            else:
                updated = "from typing import Any\n" + updated
        updated = updated + catalog_snippet

    if updated != contents:
        routing_path.write_text(updated, encoding="utf-8")


# Public module exports
__all__ = [
    "ensure_health_package",
    "synchronize_health_package",
    "ensure_vendor_health_shim",
    "HealthShimSpec",
]
