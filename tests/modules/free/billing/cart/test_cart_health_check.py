"""Health surface tests for the Cart module."""

from __future__ import annotations


def test_run_cart_health_check_returns_metrics(generated_modules) -> None:
    runtime = generated_modules["runtime"]
    health = generated_modules["health"]
    service = runtime.CartService()
    service.add_item("h1", sku="sku", name="name", quantity=1, unit_price="1.00")
    payload = health.run_cart_health_check(service)
    assert payload["status"] == "ok"
    assert payload["metrics"]["total_carts"] >= 1


def test_run_cart_health_check_handles_errors(monkeypatch, generated_modules) -> None:
    runtime = generated_modules["runtime"]
    health = generated_modules["health"]
    service = runtime.CartService()

    def boom(*_, **__):  # noqa: ANN001, D401 - test shim
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "inspect", boom)
    payload = health.run_cart_health_check(service)
    assert payload["status"] == "error"
    assert "boom" in payload.get("detail", "")
