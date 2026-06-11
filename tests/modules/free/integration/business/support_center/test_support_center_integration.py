import importlib.util
import sys
from pathlib import Path

from modules.free.business.support_center.generate import SupportCenterModuleGenerator


def _load_vendor(path: Path) -> object:
    spec = importlib.util.spec_from_file_location("integration_support_center_vendor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated vendor from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_support_center_integration_runtime_smoke(tmp_path: Path) -> None:
    generator = SupportCenterModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor = _load_vendor(
        tmp_path
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/business/support_center/support_center.py"
    )
    center = vendor.SupportCenter()
    ticket = center.open_ticket(
        subject="Download token expired",
        customer_id="cust-1",
        requester_email="customer@example.com",
    )
    resolved = center.resolve(ticket.id, actor_id="agent-1", resolution="Issued a fresh token")

    assert resolved.status == vendor.TicketStatus.RESOLVED
