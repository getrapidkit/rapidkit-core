from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.communication.webhook_platform.generate import WebhookPlatformModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_communication_webhook_platform_generates_and_delivers_signed_event(
    tmp_path: Path,
) -> None:
    generator = WebhookPlatformModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/communication/webhook_platform.py"
    )
    vendor = _load_module("integration_webhook_platform_vendor", vendor_path)

    calls = []

    def handler(url, headers, payload):  # type: ignore[no-untyped-def]
        calls.append((url, headers, payload))
        return 204, "ok"

    runtime = vendor.WebhookPlatform(handler=handler)
    endpoint = runtime.register_endpoint(
        url="https://example.com/hooks",
        secret="secret",
        events=("product.published",),
        tenant_id="tenant-1",
    )
    event = runtime.publish(
        event_type="product.published",
        payload={"product_id": "workspace-crm"},
        idempotency_key="publish-workspace-crm",
        tenant_id="tenant-1",
    )

    delivery = runtime.list_deliveries(event_id=event.id)[0]

    assert calls[0][0] == "https://example.com/hooks"
    assert delivery.endpoint_id == endpoint.id
    assert delivery.status == "delivered"
    assert vendor.verify_signature("secret", {"product_id": "workspace-crm"}, delivery.signature)
    replayed = runtime.replay_delivery(delivery.id, tenant_id="tenant-1")
    assert replayed.attempt == 2
    assert len(runtime.audit_events(event_id=event.id)) >= 4
    assert (
        runtime.publish(
            event_type="product.published",
            payload={"product_id": "ignored"},
            idempotency_key="publish-workspace-crm",
        )
        == event
    )
