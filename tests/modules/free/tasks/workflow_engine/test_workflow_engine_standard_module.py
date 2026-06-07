def test_workflow_engine_generated_runtime_is_usable(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]

    engine = vendor.WorkflowEngine()
    engine.register_task("noop", lambda _inputs, _results: "ok")
    definition = engine.register_workflow(
        vendor.WorkflowDefinition(name="noop", steps=(vendor.WorkflowStep("noop", "noop"),))
    )

    assert definition.name == "noop"
    assert engine.start("noop").status == vendor.WorkflowStatus.SUCCEEDED
