import importlib.util
import sys
from pathlib import Path

from modules.free.business.org_admin_console.generate import OrgAdminConsoleModuleGenerator


def _load_vendor(path: Path) -> object:
    spec = importlib.util.spec_from_file_location("integration_org_admin_console_vendor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated vendor from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_org_admin_console_integration_runtime_smoke(tmp_path: Path) -> None:
    generator = OrgAdminConsoleModuleGenerator()
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
        / "src/modules/free/business/org_admin_console/org_admin_console.py"
    )
    console = vendor.OrgAdminConsole()
    org = console.create_org(name="Acme", slug="acme", owner_user_id="owner")

    assert console.health()["organizations"] == 1
    assert org.slug == "acme"
