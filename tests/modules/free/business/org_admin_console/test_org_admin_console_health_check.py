def test_org_admin_console_health_reports_runtime_state(rendered_org_admin_console) -> None:
    vendor = rendered_org_admin_console["vendor"]
    console = vendor.OrgAdminConsole()
    org = console.create_org(name="Acme", slug="acme", owner_user_id="owner")
    console.invite_member(org_id=org.id, email="admin@example.com", role="admin", actor_id="owner")

    health = console.health()
    assert health["organizations"] == 1
    assert health["members"] == 1
    assert health["pending_invitations"] == 1
