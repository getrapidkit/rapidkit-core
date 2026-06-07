def test_approval_engine_health_counts_requests(rendered_approval_engine) -> None:
    vendor = rendered_approval_engine["vendor"]
    engine = vendor.ApprovalEngine()
    engine.register_policy(key="commerce.publish")
    engine.request_approval(
        policy_key="commerce.publish",
        action="publish product",
        requester_id="admin",
        reason="release gate passed",
    )

    assert engine.health()["status"] == "ok"
    assert engine.health()["pending"] == 1
