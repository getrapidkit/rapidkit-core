import importlib
import sys
from types import SimpleNamespace

import pytest

health = importlib.import_module("runtime.core.health")
# canonical runtime mapping for tests
sys.modules.setdefault("src.health", health)


def test_iter_candidate_imports_includes_dynamic(monkeypatch):
    dummy_info = SimpleNamespace(name="src.health.extra.module")
    monkeypatch.setattr(
        health.pkgutil,
        "walk_packages",
        lambda *_args, **_kwargs: [dummy_info],
    )
    monkeypatch.setattr(health, "_FALLBACK_IMPORTS", ())

    candidates = health._iter_candidate_imports()

    assert ("src.health.extra.module", "register_module_health") in candidates


def test_iter_health_registrars_uses_discovered(monkeypatch):
    probe = []

    def dummy_registrar(app):
        probe.append(app)

    monkeypatch.setattr(health, "_discover_registrars", lambda: [dummy_registrar])

    assert list(health.iter_health_registrars()) == [dummy_registrar]

    sentinel = object()
    for registrar in health.iter_health_registrars():
        registrar(sentinel)
    assert probe == [sentinel]


def test_register_health_routes_invokes_all(monkeypatch):
    calls = []

    def make_registrar(name):
        def registrar(app):
            calls.append((name, app))

        return registrar

    monkeypatch.setattr(
        health,
        "_discover_registrars",
        lambda: [make_registrar("a"), make_registrar("b")],
    )

    app = object()
    health.register_health_routes(app)

    assert calls == [("a", app), ("b", app)]


def test_list_health_routes_renders_slugs(monkeypatch):
    monkeypatch.setattr(
        health,
        "_resolve_health_modules",
        lambda: [
            ("src.health.alpha", lambda _app: None, "alpha_module"),
            ("src.health.beta", lambda _app: None, "beta"),
        ],
    )

    routes = health.list_health_routes(prefix="/status")

    assert routes == [
        {
            "module_path": "src.health.alpha",
            "slug": "alpha_module",
            "path": "/status/module/alpha-module",
        },
        {
            "module_path": "src.health.beta",
            "slug": "beta",
            "path": "/status/module/beta",
        },
    ]


@pytest.mark.parametrize("registrars", [[], [lambda _app: None]])
def test_iter_health_registrars_yields_from_cache(monkeypatch, registrars):
    monkeypatch.setattr(health, "_discover_registrars", lambda: registrars)
    assert list(health.iter_health_registrars()) == registrars
