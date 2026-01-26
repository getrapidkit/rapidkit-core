from src.modules.free.communication.notifications.core.notifications import (
    NotificationManager,
    list_notification_features,
)


def test_notifications_runtime_imports_and_exposes_features():
    manager = NotificationManager()
    async def _noop_handler(notification):
        return True

    assert list(manager.available_channels()) == []
    manager.register_handler("noop", _noop_handler)
    assert "noop" in list(manager.available_channels())

    features = list_notification_features()
    assert "email_channel" in features
