from __future__ import annotations

import pytest


def test_org_admin_console_handles_org_membership_and_settings(rendered_org_admin_console) -> None:
    vendor = rendered_org_admin_console["vendor"]
    console = vendor.OrgAdminConsole()
    org = console.create_org(name="Acme", slug="acme", owner_user_id="owner-1")
    invite = console.invite_member(
        org_id=org.id, email="admin@example.com", role="admin", actor_id="owner-1"
    )
    member = console.accept_invite(invite.id, user_id="admin-2")
    updated = console.update_role(member.id, role="viewer", actor_id="owner-1")
    settings = console.update_settings(
        org.id, settings={"domain": "acme.example"}, actor_id="owner-1"
    )

    assert updated.role == "viewer"
    assert settings.settings["domain"] == "acme.example"
    assert len(console.list_members(org.id)) == 2
    assert console.health()["pending_invitations"] == 0
    assert [event["type"] for event in console.audit_events(org_id=org.id)] == [
        "org.created",
        "member.invited",
        "member.joined",
        "member.role_updated",
        "org.settings_updated",
    ]


def test_org_admin_console_rejects_duplicate_slug_and_bad_role(rendered_org_admin_console) -> None:
    vendor = rendered_org_admin_console["vendor"]
    console = vendor.OrgAdminConsole()
    org = console.create_org(name="Acme", slug="acme", owner_user_id="owner-1")

    with pytest.raises(vendor.OrgAdminConsoleError, match="slug"):
        console.create_org(name="Acme 2", slug="acme", owner_user_id="owner-2")
    with pytest.raises(vendor.OrgAdminConsoleError, match="role"):
        console.invite_member(
            org_id=org.id, email="user@example.com", role="root", actor_id="owner-1"
        )
