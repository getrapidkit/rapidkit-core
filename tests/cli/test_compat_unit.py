from cli import _compat


def test_safe_echo_sanitizes(monkeypatch):
    calls = {}

    def fake_sanitize(message: str) -> str:
        calls["message"] = message
        return "sanitized"

    monkeypatch.setattr(_compat, "_sanitize_console_text", fake_sanitize, raising=False)

    emitted = {}

    def fake_click_echo(*, message=None, **_kwargs):
        emitted["message"] = message

    monkeypatch.setattr(_compat, "_click_echo", fake_click_echo, raising=False)

    _compat.click.echo("raw output")

    assert calls["message"] == "raw output"
    assert emitted["message"] == "sanitized"


def test_click_echo_passes_kwargs(monkeypatch):
    recorded = {}

    def fake_click_echo(**kwargs):
        recorded.update(kwargs)

    monkeypatch.setattr(_compat, "_click_echo", fake_click_echo, raising=False)

    _compat.click.echo("payload", file="stream", nl=False, err=True, color="blue")

    assert recorded == {
        "message": "payload",
        "file": "stream",
        "nl": False,
        "err": True,
        "color": "blue",
    }
