from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.business.multi_tenancy.generate import MultiTenancyModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_business_multi_tenancy_generates_and_enforces_tenant_roles(tmp_path: Path) -> None:
    generator = MultiTenancyModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/business/multi_tenancy.py"
    )
    vendor = _load_module("integration_multi_tenancy_vendor", vendor_path)

    runtime = vendor.MultiTenancy()
    tenant = runtime.create_tenant(name="Acme Inc", owner_user_id="owner-1")
    runtime.assign_role(
        tenant_id=tenant.id,
        user_id="member-1",
        role=vendor.TenantRole.MEMBER,
    )
    context = runtime.require_role(
        tenant_id=tenant.id,
        user_id="owner-1",
        minimum_role=vendor.TenantRole.ADMIN,
    )

    assert context.role == vendor.TenantRole.OWNER
    assert context.isolation_key == f"tenant:{tenant.id}"
    assert [member.user_id for member in runtime.list_members(tenant.id)] == [
        "owner-1",
        "member-1",
    ]
    assert len(runtime.audit_events(tenant.id)) >= 3
