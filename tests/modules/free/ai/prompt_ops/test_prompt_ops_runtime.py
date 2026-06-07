import pytest


def test_prompt_ops_versions_publishes_and_renders(rendered_prompt_ops) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_prompt_ops["vendor"]

    ops = vendor.PromptOps()
    created = ops.create_prompt("support.reply", "Hello $name, ticket $ticket_id is ready")

    with pytest.raises(vendor.PromptOpsError):
        ops.publish("support.reply", created.version)

    published = ops.publish("support.reply", created.version, approved_by="admin@example.com")
    ops.record_evaluation("support.reply", published.version, score=0.94, passed=True)

    assert published.status == vendor.PromptStatus.PUBLISHED
    assert (
        ops.render("support.reply", {"name": "Ada", "ticket_id": "T-1"})
        == "Hello Ada, ticket T-1 is ready"
    )
    assert ops.health_check()["published"] == 1
    assert ops.evaluations("support.reply")[0].passed is True


def test_prompt_ops_rolls_back_with_audit_reason(rendered_prompt_ops) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_prompt_ops["vendor"]

    ops = vendor.PromptOps(vendor.PromptOpsConfig(require_approval_for_publish=False))
    ops.publish("agent.plan", ops.create_prompt("agent.plan", "Plan v1").version)
    ops.publish("agent.plan", ops.create_prompt("agent.plan", "Plan v2").version)

    rollback = ops.rollback("agent.plan", 1, reason="v2 quality regression")

    assert rollback.version == 3
    assert rollback.template == "Plan v1"
    assert ops.audit_log()[-1]["event"] == "prompt.rollback"
