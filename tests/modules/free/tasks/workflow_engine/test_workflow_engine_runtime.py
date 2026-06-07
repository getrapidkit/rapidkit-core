def test_workflow_engine_executes_steps_in_order(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine()
    engine.register_task("extract", lambda inputs, _results: inputs["value"] + 1)
    engine.register_task("load", lambda _inputs, results: results["extract"].output * 2)
    engine.register_workflow(
        vendor.WorkflowDefinition(
            name="etl",
            steps=(
                vendor.WorkflowStep(name="extract", task="extract"),
                vendor.WorkflowStep(name="load", task="load", depends_on=("extract",)),
            ),
        )
    )

    run = engine.start("etl", inputs={"value": 2})

    assert run.status == vendor.WorkflowStatus.SUCCEEDED
    assert [result.output for result in run.results] == [3, 6]
    assert [event.type for event in engine.events(run.id)] == [
        "run.started",
        "step.started",
        "step.succeeded",
        "step.started",
        "step.succeeded",
        "run.succeeded",
    ]


def test_workflow_engine_retries_failed_steps(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine()
    attempts = {"count": 0}

    def flaky(_inputs, _results):  # type: ignore[no-untyped-def]
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("try again")
        return "ok"

    engine.register_task("flaky", flaky)
    engine.register_workflow(
        vendor.WorkflowDefinition(
            name="retry",
            steps=(vendor.WorkflowStep(name="flaky", task="flaky", max_retries=1),),
        )
    )

    run = engine.start("retry")

    assert run.status == vendor.WorkflowStatus.SUCCEEDED
    assert run.results[0].attempts == 2
