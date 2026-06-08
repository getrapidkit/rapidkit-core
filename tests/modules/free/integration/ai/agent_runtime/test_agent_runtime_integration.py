from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.ai.agent_runtime.generate import AgentRuntimeModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_ai_agent_runtime_generates_and_executes_tool_plan(tmp_path: Path) -> None:
    generator = AgentRuntimeModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/ai/agent_runtime/agent_runtime.py"
    )
    vendor = _load_module("integration_agent_runtime_vendor", vendor_path)

    def approve(arguments, run):  # type: ignore[no-untyped-def]
        return {"approved": bool(arguments["ready"]), "objective": run.objective}

    runtime = vendor.AgentRuntime(tools={"approve": approve})
    run = runtime.create_run("Validate release readiness", tenant_id="tenant-1")
    completed = runtime.execute(run.run_id, [vendor.AgentToolCall("approve", {"ready": True})])

    assert completed.status == vendor.AgentRunStatus.SUCCEEDED
    assert completed.steps[0].output["approved"] is True
    assert runtime.list_runs(tenant_id="tenant-1") == [completed]
