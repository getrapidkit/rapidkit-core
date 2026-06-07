import pytest


def test_workflow_engine_rejects_duplicate_steps(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine()

    with pytest.raises(vendor.WorkflowEngineError, match="unique"):
        engine.register_workflow(
            vendor.WorkflowDefinition(
                name="bad",
                steps=(
                    vendor.WorkflowStep(name="same", task="x"),
                    vendor.WorkflowStep(name="same", task="y"),
                ),
            )
        )


def test_workflow_engine_rejects_disabled_runtime(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine(vendor.WorkflowEngineConfig(enabled=False))

    with pytest.raises(vendor.WorkflowEngineError, match="disabled"):
        engine.register_workflow(
            vendor.WorkflowDefinition(name="x", steps=(vendor.WorkflowStep("x", "x"),))
        )
