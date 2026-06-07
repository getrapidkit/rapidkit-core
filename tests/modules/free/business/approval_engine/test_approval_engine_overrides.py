from modules.free.business.approval_engine import overrides


def test_approval_engine_overrides_contract_loads() -> None:
    assert hasattr(overrides, "ApprovalEngineOverrides")
