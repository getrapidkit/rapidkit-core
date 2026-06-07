import pytest


def test_workflow_engine_fails_missing_task_handler(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine()
    engine.register_workflow(
        vendor.WorkflowDefinition(
            name="missing",
            steps=(vendor.WorkflowStep(name="step", task="missing"),),
        )
    )

    run = engine.start("missing")

    assert run.status == vendor.WorkflowStatus.FAILED
    assert run.results[0].error == "task handler not found"


def test_workflow_engine_rejects_unknown_workflow(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine()

    with pytest.raises(vendor.WorkflowEngineError, match="workflow not found"):
        engine.start("missing")


def test_workflow_engine_rejects_dependency_on_future_step(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine()

    with pytest.raises(vendor.WorkflowEngineError, match="future or unknown steps"):
        engine.register_workflow(
            vendor.WorkflowDefinition(
                name="bad-order",
                steps=(
                    vendor.WorkflowStep(name="second", task="noop", depends_on=("first",)),
                    vendor.WorkflowStep(name="first", task="noop"),
                ),
            )
        )
