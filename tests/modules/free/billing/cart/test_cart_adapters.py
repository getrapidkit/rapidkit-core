"""Adapter integration tests for the Cart module."""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_fastapi_routes_handle_crud(generated_modules) -> None:
    runtime = generated_modules["runtime"]
    routers = importlib.import_module("src.modules.free.billing.cart.routers.cart")

    app = FastAPI()
    routers.register_cart(app, service=runtime.CartService())
    client = TestClient(app)

    response = client.post(
        "/api/cart/test/items",
        json={
            "sku": "sku",
            "name": "Sample",
            "quantity": 2,
            "unit_price": "12.50",
            "currency": "USD",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["totals"]["subtotal"] == "25.00"

    response = client.get("/api/cart/test")
    assert response.status_code == 200

    response = client.post("/api/cart/test/discounts/WELCOME", json={"force": True})
    assert response.status_code == 200

    response = client.delete("/api/cart/test/items/sku")
    assert response.status_code == 200
