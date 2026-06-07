import pytest


def test_support_center_ticket_validation(rendered_support_center) -> None:
    vendor = rendered_support_center["vendor"]
    center = vendor.SupportCenter()

    with pytest.raises(vendor.SupportCenterError, match="subject"):
        center.open_ticket(subject="", customer_id="cust", requester_email="user@example.com")
