from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.security.audit_policy.generate import AuditPolicyModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_security_audit_policy_generates_append_only_hash_chain(tmp_path: Path) -> None:
    generator = AuditPolicyModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/security/audit_policy.py"
    )
    vendor = _load_module("integration_audit_policy_vendor", vendor_path)

    runtime = vendor.AuditPolicy()
    first = runtime.record(
        action="product.publish",
        actor_id="admin-1",
        role="admin",
        resource="product:crm",
        reason="release approved",
        tenant_id="tenant-a",
    )
    second = runtime.record(
        action="entitlement.assign",
        actor_id="admin-1",
        role="admin",
        resource="entitlement:crm",
        reason="purchase completed",
        tenant_id="tenant-a",
    )

    assert second.previous_hash == first.event_hash
    assert runtime.verify_chain() is True
    assert [event.action for event in runtime.list_events(tenant_id="tenant-a")] == [
        "product.publish",
        "entitlement.assign",
    ]
