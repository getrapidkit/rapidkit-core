from modules.free.security.audit_policy.overrides import AuditPolicyOverrides


def test_audit_policy_overrides_are_configurable() -> None:
    overrides = AuditPolicyOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
