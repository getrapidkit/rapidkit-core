from pathlib import Path

from modules.free.billing.usage_billing.generate import UsageBillingModuleGenerator


def test_usage_billing_renders_fastapi_and_nestjs_variants(tmp_path: Path) -> None:
    generator = UsageBillingModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    fastapi_dir = tmp_path / "fastapi"
    nestjs_dir = tmp_path / "nestjs"
    generator.generate_vendor_files(config, fastapi_dir, renderer, context)
    generator.generate_variant_files("fastapi", fastapi_dir, renderer, context)
    generator.generate_vendor_files(
        config, nestjs_dir, renderer, {**context, "framework": "nestjs"}
    )
    generator.generate_variant_files("nestjs", nestjs_dir, renderer, context)

    assert (fastapi_dir / "src" / "billing" / "usage_billing.py").exists()
    assert (fastapi_dir / "src" / "routers" / "billing" / "usage_billing.py").exists()
    assert (nestjs_dir / "src" / "usage-billing" / "usage_billing.service.ts").exists()
