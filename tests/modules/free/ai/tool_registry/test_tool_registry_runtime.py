def test_tool_registry_allows_scoped_tool(rendered_tool_registry) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_tool_registry["vendor"]

    registry = vendor.ToolRegistry()
    registry.register_tool(
        vendor.ToolDefinition(
            name="search_docs",
            description="Search tenant documents",
            scopes=("docs:read",),
            roles=("support",),
            risk=vendor.ToolRisk.MEDIUM,
        )
    )

    decision = registry.evaluate(
        "search_docs",
        vendor.ToolInvocationPolicy(
            tenant_id="tenant-1",
            user_id="user-1",
            scopes=("docs:read",),
            roles=("support",),
        ),
    )

    assert decision.allowed is True
    assert decision.reason == "allowed"
    assert registry.health_check()["tools"] == 1
    assert registry.audit_log()[-1]["event"] == "tool.evaluated"


def test_tool_registry_blocks_high_risk_without_override(rendered_tool_registry) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_tool_registry["vendor"]

    registry = vendor.ToolRegistry()
    registry.register_tool(
        vendor.ToolDefinition(
            name="delete_customer",
            description="Delete customer data",
            scopes=("customers:write",),
            roles=("admin",),
            risk=vendor.ToolRisk.HIGH,
        )
    )

    decision = registry.evaluate(
        "delete_customer",
        vendor.ToolInvocationPolicy(scopes=("customers:write",), roles=("admin",)),
    )

    assert decision.allowed is False
    assert decision.reason == "high_risk_tool_requires_explicit_allow"
