from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.business.connector_hub.generate import ConnectorHubModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_business_connector_hub_generates_and_runs_connector_operation(
    tmp_path: Path,
) -> None:
    generator = ConnectorHubModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/business/connector_hub.py"
    )
    vendor = _load_module("integration_connector_hub_vendor", vendor_path)

    hub = vendor.ConnectorHub()
    hub.register_connector(
        vendor.ConnectorDefinition(
            key="stripe",
            display_name="Stripe",
            operations=("sync_customer",),
            required_secrets=("api_key",),
        ),
        handlers={"sync_customer": lambda payload, context: {"synced": payload["id"], **context}},
    )
    connection = hub.connect(
        connector="stripe",
        tenant_id="tenant-a",
        secrets={"api_key": "sk_test"},
        config={"mode": "test"},
    )

    run = hub.execute(
        connection_id=connection.id,
        operation="sync_customer",
        payload={"id": "cus_1"},
        tenant_id="tenant-a",
        idempotency_key="sync-cus-1",
    )
    repeated = hub.execute(
        connection_id=connection.id,
        operation="sync_customer",
        payload={"id": "cus_1"},
        tenant_id="tenant-a",
        idempotency_key="sync-cus-1",
    )

    assert run.status == "succeeded"
    assert repeated.id == run.id
    assert run.output["synced"] == "cus_1"
    assert run.output["connection"]["secrets"] == {"api_key": "***"}
    assert hub.health()["stats"]["runs"] == 1
    assert len(hub.audit_events(connection_id=connection.id)) >= 2
