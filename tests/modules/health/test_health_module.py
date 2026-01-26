import importlib
import sys
from types import SimpleNamespace

health_module = importlib.import_module("runtime.core.health")
sys.modules.setdefault("src.health", health_module)


def test_iter_candidate_imports_adds_sorted_dynamic_modules(monkeypatch):
    discovered = [
        SimpleNamespace(name=f"{health_module.__name__}.zeta"),
        SimpleNamespace(name=f"{health_module.__name__}.alpha"),
        SimpleNamespace(name=f"{health_module.__name__}.alpha"),
    ]

    def fake_walk_packages(_path, prefix):
        assert prefix == f"{health_module.__name__}."
        return iter(discovered)

    monkeypatch.setattr(health_module.pkgutil, "walk_packages", fake_walk_packages)

    candidate_imports = health_module._iter_candidate_imports()

    fallback = set(health_module._FALLBACK_IMPORTS)
    dynamic_candidates = [
        candidate
        for candidate in candidate_imports
        if candidate[0].startswith(f"{health_module.__name__}.") and candidate not in fallback
    ]

    assert dynamic_candidates == [
        (f"{health_module.__name__}.alpha", "register_alpha_health"),
        (f"{health_module.__name__}.zeta", "register_zeta_health"),
    ]


def test_resolve_health_modules_skips_missing_and_noncallable(monkeypatch):
    monkeypatch.setattr(
        health_module,
        "_iter_candidate_imports",
        lambda: [
            ("core.health.alpha", "register_alpha_health"),
            ("core.health.beta", "register_beta_health"),
            ("core.health.gamma", "register_gamma_health"),
            ("core.health.delta", "register_delta_health"),
        ],
    )

    imported_modules = {
        "core.health.alpha": SimpleNamespace(register_alpha_health=lambda _app: None),
        "core.health.beta": SimpleNamespace(register_beta_health="not-callable"),
        "core.health.delta": SimpleNamespace(),
    }

    def fake_import(name):
        if name == "core.health.gamma":
            raise ImportError("gamma boom")
        module = imported_modules.get(name)
        if module is None:
            raise ImportError(name)
        return module

    monkeypatch.setattr(health_module, "import_module", fake_import)

    resolved = health_module._resolve_health_modules()

    assert resolved == [
        (
            "core.health.alpha",
            imported_modules["core.health.alpha"].register_alpha_health,
            "alpha",
        )
    ]


def test_register_health_routes_invokes_each_registrar(monkeypatch):
    recorded_calls: list[str] = []

    def registrar_one(app):
        recorded_calls.append(f"one:{app}")

    def registrar_two(app):
        recorded_calls.append(f"two:{app}")

    monkeypatch.setattr(
        health_module, "_discover_registrars", lambda: [registrar_one, registrar_two]
    )

    health_module.register_health_routes(app="app-instance")

    assert recorded_calls == ["one:app-instance", "two:app-instance"]


def test_list_health_routes_returns_expected_metadata(monkeypatch):
    sentinel_registrar = object()
    monkeypatch.setattr(
        health_module,
        "_resolve_health_modules",
        lambda: [
            ("core.health.alpha", sentinel_registrar, "alpha"),
            ("core.health.beta_service", sentinel_registrar, "beta_service"),
        ],
    )

    routes = health_module.list_health_routes(prefix="/healthz")

    assert routes == [
        {
            "module_path": "core.health.alpha",
            "slug": "alpha",
            "path": "/healthz/module/alpha",
        },
        {
            "module_path": "core.health.beta_service",
            "slug": "beta_service",
            "path": "/healthz/module/beta-service",
        },
    ]
