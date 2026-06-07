def test_workflow_engine_lists_runs_by_status(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine()
    engine.register_task("noop", lambda _inputs, _results: None)
    engine.register_workflow(
        vendor.WorkflowDefinition(name="noop", steps=(vendor.WorkflowStep("noop", "noop"),))
    )
    engine.start("noop")

    assert len(engine.list_runs(status=vendor.WorkflowStatus.SUCCEEDED)) == 1
    assert engine.list_runs(status=vendor.WorkflowStatus.FAILED) == ()
