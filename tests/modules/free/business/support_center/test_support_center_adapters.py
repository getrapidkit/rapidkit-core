def test_support_center_exposes_runtime_contract(rendered_support_center) -> None:
    vendor = rendered_support_center["vendor"]

    assert hasattr(vendor, "SupportCenter")
    assert hasattr(vendor, "SupportTicket")
    assert hasattr(vendor, "TicketStatus")
