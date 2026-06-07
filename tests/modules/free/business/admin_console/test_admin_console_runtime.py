from __future__ import annotations

import pytest


def test_admin_console_runs_authorized_actions_with_reason(rendered_admin_console) -> None:
    vendor = rendered_admin_console["vendor"]
    console = vendor.AdminConsole()
    console.register_action(
        vendor.AdminAction(
            key="commerce.publish",
            label="Publish product",
            required_roles=("publisher",),
            dangerous=True,
        ),
        handler=lambda payload: {"published": payload["product_id"]},
    )

    with pytest.raises(vendor.AdminConsoleError, match="reason"):
        console.run_action(
            "commerce.publish",
            actor_id="admin-1",
            actor_role="publisher",
            reason="",
            payload={"product_id": "prod-1"},
        )

    run = console.run_action(
        "commerce.publish",
        actor_id="admin-1",
        actor_role="publisher",
        reason="release gate passed",
        payload={"product_id": "prod-1"},
        tenant_id="tenant-1",
    )

    assert run.status == "succeeded"
    assert run.result == {"published": "prod-1"}
    assert console.summary()["dangerous_actions"] == 1


def test_admin_console_blocks_wrong_roles(rendered_admin_console) -> None:
    vendor = rendered_admin_console["vendor"]
    console = vendor.AdminConsole()
    console.register_action(
        vendor.AdminAction(key="backup.import", label="Import backup", required_roles=("ops",))
    )

    with pytest.raises(vendor.AdminConsoleError, match="role"):
        console.run_action(
            "backup.import", actor_id="support-1", actor_role="support", reason="restore"
        )
