import importlib.util
import sys
from pathlib import Path

from modules.free.business.forms_engine.generate import FormsEngineModuleGenerator


def _load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_forms_engine_integration_workflow_hook(tmp_path: Path) -> None:
    generator = FormsEngineModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor = _load_module(
        "integration_forms_engine_vendor",
        tmp_path
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src"
        / "business"
        / "forms_engine.py",
    )
    captured = []
    engine = vendor.FormsEngine(
        workflow_hook=lambda submission: captured.append(submission.submission_id)
    )
    form = engine.create_form(
        "Contact", [vendor.FormField("email", "Email", vendor.FieldType.EMAIL, required=True)]
    )

    submission = engine.submit(form.form_id, {"email": "ok@example.com"})

    assert captured == [submission.submission_id]
