from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.business.feature_flags.generate import FeatureFlagsModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_business_feature_flags_generates_and_evaluates_rules(tmp_path: Path) -> None:
    generator = FeatureFlagsModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/business/feature_flags.py"
    )
    vendor = _load_module("integration_feature_flags_vendor", vendor_path)

    runtime = vendor.FeatureFlags()
    runtime.upsert_flag(
        key="enterprise-checkout",
        default=False,
        rules=(
            vendor.FlagRule(
                attribute="plan",
                operator="equals",
                values=("enterprise",),
                variation=True,
            ),
        ),
        tenant_overrides={"tenant-a": True},
    )

    tenant_eval = runtime.evaluate(
        "enterprise-checkout",
        context=vendor.EvaluationContext(tenant_id="tenant-a"),
    )
    rule_eval = runtime.evaluate(
        "enterprise-checkout",
        context=vendor.EvaluationContext(attributes={"plan": "enterprise"}),
    )

    assert tenant_eval.value is True
    assert tenant_eval.reason == "tenant_override"
    assert rule_eval.value is True
    assert rule_eval.reason == "rule"
