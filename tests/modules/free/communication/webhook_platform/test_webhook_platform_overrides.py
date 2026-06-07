from modules.free.communication.webhook_platform.overrides import WebhookPlatformOverrides


def test_webhook_platform_overrides_are_configurable() -> None:
    overrides = WebhookPlatformOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
