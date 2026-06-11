import pytest

from cli.utils.module_identity import module_identity_matches


@pytest.mark.parametrize(
    ("recorded", "requested", "expected"),
    [
        ("agent_runtime", "free/ai/agent_runtime", True),
        ("llm_gateway", "free/ai/llm_gateway", True),
        ("free/ai/agent_runtime", "free/ai/agent_runtime", True),
        ("settings", "free/essentials/settings", True),
        ("logging", "free/essentials/logging", True),
        ("agent_runtime", "free/ai/llm_gateway", False),
        (None, "free/ai/agent_runtime", False),
        ("agent_runtime", "", False),
    ],
)
def test_module_identity_matches(recorded, requested, expected) -> None:
    assert module_identity_matches(recorded, requested) is expected
