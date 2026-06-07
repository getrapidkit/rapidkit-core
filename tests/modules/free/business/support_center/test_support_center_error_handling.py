import pytest


def test_support_center_rejects_missing_ticket(rendered_support_center) -> None:
    vendor = rendered_support_center["vendor"]
    center = vendor.SupportCenter()

    with pytest.raises(vendor.SupportCenterError, match="ticket not found"):
        center.assign("missing", agent_id="agent", actor_id="lead")
