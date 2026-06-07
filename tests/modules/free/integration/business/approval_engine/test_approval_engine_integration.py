import importlib.util
import sys
from pathlib import Path

from modules.free.business.approval_engine.generate import ApprovalEngineModuleGenerator


def _load_vendor(path: Path) -> object:
    spec = importlib.util.spec_from_file_location("integration_approval_engine_vendor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated vendor from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_approval_engine_integration_runtime_smoke(tmp_path: Path) -> None:
    generator = ApprovalEngineModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor = _load_vendor(
        tmp_path
        / ".rapidkit"
        / "vendor"
        / "approval_engine"
        / "0.1.3"
        / "src/business/approval_engine.py"
    )
    engine = vendor.ApprovalEngine()
    engine.register_policy(key="publish", required_roles=("publisher",))
    request = engine.request_approval(
        policy_key="publish",
        action="publish product",
        requester_id="admin",
        reason="release gate passed",
    )
    approved = engine.decide(
        request.id,
        reviewer_id="owner",
        reviewer_role="publisher",
        approved=True,
        reason="approved for release",
    )

    assert approved.status == vendor.ApprovalStatus.APPROVED
