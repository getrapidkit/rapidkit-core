from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.tasks.workflow_engine.generate import WorkflowEngineModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_tasks_workflow_engine_generates_and_runs_release_workflow(tmp_path: Path) -> None:
    generator = WorkflowEngineModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/tasks/workflow_engine/workflow_engine.py"
    )
    vendor = _load_module("integration_workflow_engine_vendor", vendor_path)

    engine = vendor.WorkflowEngine()
    engine.register_task("score", lambda inputs, _results: inputs["readiness"] + 10)
    engine.register_task("publish", lambda _inputs, results: results["score"].output >= 90)
    engine.register_workflow(
        vendor.WorkflowDefinition(
            name="release",
            steps=(
                vendor.WorkflowStep(name="score", task="score"),
                vendor.WorkflowStep(name="publish", task="publish", depends_on=("score",)),
            ),
        )
    )

    run = engine.start("release", inputs={"readiness": 82})

    assert run.status == vendor.WorkflowStatus.SUCCEEDED
    assert [result.output for result in run.results] == [92, True]
    assert [event.type for event in engine.events(run.id)] == [
        "run.started",
        "step.started",
        "step.succeeded",
        "step.started",
        "step.succeeded",
        "run.succeeded",
    ]
