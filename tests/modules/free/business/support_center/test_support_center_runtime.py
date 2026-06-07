from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


def test_support_center_ticket_lifecycle_is_audited(rendered_support_center) -> None:
    vendor = rendered_support_center["vendor"]
    center = vendor.SupportCenter(vendor.SupportCenterConfig(default_sla_hours=2))

    ticket = center.open_ticket(
        subject="Cannot download purchased workspace",
        customer_id="cust-1",
        requester_email="customer@example.com",
        priority=vendor.TicketPriority.HIGH,
        tenant_id="tenant-1",
        tags=("commerce", "download"),
    )
    assigned = center.assign(ticket.id, agent_id="agent-1", actor_id="lead-1")
    note = center.add_note(ticket.id, author_id="agent-1", body="Token was expired", internal=True)
    resolved = center.resolve(
        ticket.id, actor_id="agent-1", resolution="Issued a fresh download token"
    )
    closed = center.close(ticket.id, actor_id="lead-1")

    assert assigned.status == vendor.TicketStatus.PENDING
    assert note.internal is True
    assert resolved.status == vendor.TicketStatus.RESOLVED
    assert closed.status == vendor.TicketStatus.CLOSED
    assert len(center.list_notes(ticket.id)) == 2
    assert [event.type for event in center.audit_events(ticket_id=ticket.id)] == [
        "ticket.opened",
        "ticket.assigned",
        "ticket.note_added",
        "ticket.note_added",
        "ticket.resolved",
        "ticket.closed",
    ]


def test_support_center_sla_and_validation(rendered_support_center) -> None:
    vendor = rendered_support_center["vendor"]
    center = vendor.SupportCenter(vendor.SupportCenterConfig(default_sla_hours=1))

    with pytest.raises(vendor.SupportCenterError, match="requester_email"):
        center.open_ticket(
            subject="Broken",
            customer_id="cust-1",
            requester_email="not-an-email",
        )

    ticket = center.open_ticket(
        subject="Webhook history missing",
        customer_id="cust-2",
        requester_email="ops@example.com",
        priority="urgent",
    )
    later = datetime.now(timezone.utc) + timedelta(hours=2)

    assert center.sla_breaches(now=later) == (ticket,)
    assert center.health()["open"] == 1
