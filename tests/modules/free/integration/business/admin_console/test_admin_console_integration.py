import importlib.util
import sys
from pathlib import Path

from modules.free.business.admin_console.generate import AdminConsoleModuleGenerator


def _load_vendor(path: Path) -> object:
    spec = importlib.util.spec_from_file_location("integration_admin_console_vendor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated vendor from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_admin_console_integration_runtime_smoke(tmp_path: Path) -> None:
    generator = AdminConsoleModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor = _load_vendor(
        tmp_path
        / ".rapidkit"
        / "vendor"
        / "admin_console"
        / "0.1.3"
        / "src/business/admin_console.py"
    )
    console = vendor.AdminConsole()
    console.register_action(vendor.AdminAction(key="publish", label="Publish"))
    run = console.run_action("publish", actor_id="admin", actor_role="admin", reason="release")

    assert run.status == "succeeded"
