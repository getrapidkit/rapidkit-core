from modules.free.ai.agent_runtime.overrides import AgentRuntimeOverrides


def test_agent_runtime_overrides_are_configurable() -> None:
    overrides = AgentRuntimeOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
