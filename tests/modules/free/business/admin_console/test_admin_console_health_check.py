def test_admin_console_health_reports_runtime_state(rendered_admin_console) -> None:
    vendor = rendered_admin_console["vendor"]
    console = vendor.AdminConsole()
    console.register_action(vendor.AdminAction(key="publish", label="Publish"))
    run = console.run_action("publish", actor_id="admin-1", actor_role="admin", reason="release")

    assert run.status == "succeeded"
    assert console.health()["actions"] == 1
    assert console.health()["runs"] == 1
