from modules.free.tasks.workflow_engine.overrides import WorkflowEngineOverrides


def test_workflow_engine_overrides_are_configurable() -> None:
    overrides = WorkflowEngineOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
