def test_workflow_engine_health_reports_runtime_stats(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]
    engine = vendor.WorkflowEngine()
    engine.register_task("noop", lambda _inputs, _results: None)
    engine.register_workflow(
        vendor.WorkflowDefinition(name="noop", steps=(vendor.WorkflowStep("noop", "noop"),))
    )
    engine.start("noop")

    health = engine.health()

    assert health["module"] == "workflow_engine"
    assert health["status"] == "ok"
    assert health["stats"]["workflows"] == 1
    assert health["stats"]["runs"] == 1
    assert health["stats"]["by_status"] == {"succeeded": 1}
