def test_workflow_engine_vendor_exports_runtime_contract(rendered_workflow_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_workflow_engine["vendor"]

    for name in (
        "WorkflowEngine",
        "WorkflowEngineConfig",
        "WorkflowEngineError",
        "WorkflowStatus",
        "WorkflowStep",
        "WorkflowDefinition",
        "WorkflowRun",
        "StepResult",
        "WorkflowEvent",
    ):
        assert hasattr(vendor, name)
