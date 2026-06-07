def test_support_center_health_counts_open_tickets(rendered_support_center) -> None:
    vendor = rendered_support_center["vendor"]
    center = vendor.SupportCenter()
    center.open_ticket(subject="Help", customer_id="cust", requester_email="user@example.com")

    assert center.health()["status"] == "ok"
    assert center.health()["open"] == 1
