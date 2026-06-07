from pathlib import Path

from modules.free.security.audit_policy.generate import AuditPolicyModuleGenerator


def test_audit_policy_renders_fastapi_and_nestjs_variants(tmp_path: Path) -> None:
    generator = AuditPolicyModuleGenerator()
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

    assert (fastapi_dir / "src" / "security" / "audit_policy.py").exists()
    assert (fastapi_dir / "src" / "routers" / "security" / "audit_policy.py").exists()
    assert (nestjs_dir / "src" / "audit-policy" / "audit_policy.service.ts").exists()
