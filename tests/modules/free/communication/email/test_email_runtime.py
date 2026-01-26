import asyncio
import sys
from email.message import EmailMessage
from importlib import import_module, util as import_util
from pathlib import Path

import pytest

pytest.importorskip("pydantic")


@pytest.fixture(scope="module")
def email_runtime(tmp_path_factory: pytest.TempPathFactory):
    generator = import_module("modules.free.communication.email.generate")
    renderer = generator.create_renderer()
    jinja_env = getattr(renderer, "jinja_env", None) or getattr(renderer, "_env", None)
    if jinja_env is None:
        pytest.skip("jinja2 is required to render Email templates")

    config = generator.load_module_config()
    context = generator.build_base_context(config)

    target_dir = tmp_path_factory.mktemp("email_generated")
    generator.generate_vendor_files(config, target_dir, renderer, context)
    generator.generate_variant_files(config, "fastapi", target_dir, renderer, context)

    runtime_path = target_dir / "src" / "modules" / "free" / "communication" / "email" / "email.py"
    assert runtime_path.exists(), f"Expected generated email runtime at {runtime_path}"

    spec = import_util.spec_from_file_location("rapidkit_test_email_runtime", runtime_path)
    if spec is None or spec.loader is None:
        pytest.fail("Unable to load generated email runtime module")
    module = import_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _TransportRecorder:
    def __init__(self) -> None:
        self.message = None
        self.call_count = 0

    async def __call__(self, message):  # type: ignore[override]
        self.message = message
        self.call_count += 1
        return "msg-1"


def test_email_service_uses_custom_transport(email_runtime) -> None:
    EmailConfig = email_runtime.EmailConfig
    EmailService = email_runtime.EmailService
    EmailMessagePayload = email_runtime.EmailMessagePayload

    transport = _TransportRecorder()
    config = EmailConfig(
        enabled=True,
        provider="smtp",
    )
    service = EmailService(config, transport=transport)

    payload = EmailMessagePayload(
        to=["alice@example.com"],
        subject="Hello",
        text_body="Test message",
    )

    result = asyncio.run(service.send_email(payload))

    assert result.accepted is True
    assert transport.call_count == 1
    assert transport.message["To"] == "alice@example.com"
    assert transport.message.get_body().get_content() == "Test message\n"


def test_email_service_renders_templates(tmp_path: Path, email_runtime) -> None:
    EmailConfig = email_runtime.EmailConfig
    EmailService = email_runtime.EmailService
    TemplateSettings = email_runtime.TemplateSettings

    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "welcome.html").write_text("<p>Welcome, {{ name }}!</p>", encoding="utf-8")

    config = EmailConfig(
        enabled=True,
        provider="console",
        template=TemplateSettings(directory=template_dir, auto_reload=True),
    )
    transport = _TransportRecorder()
    service = EmailService(config, transport=transport)

    result = asyncio.run(
        service.send_templated_email(
            ["team@example.com"],
            template_name="welcome.html",
            context={"name": "Bob"},
            subject="Welcome",
        )
    )

    assert result.accepted is True
    assert "Welcome, Bob" in transport.message.get_body().get_content()


def test_register_and_resolve_service_dependency(email_runtime) -> None:
    fastapi = pytest.importorskip("fastapi")
    starlette_requests = pytest.importorskip("starlette.requests")

    FastAPI = fastapi.FastAPI
    Request = starlette_requests.Request

    EmailSettings = email_runtime.EmailSettings
    EmailService = email_runtime.EmailService
    EmailMessagePayload = email_runtime.EmailMessagePayload
    register_email_service = email_runtime.register_email_service
    get_email_service = email_runtime.get_email_service

    app = FastAPI()
    transport = _TransportRecorder()
    settings = EmailSettings(provider="console", enabled=True)

    service = register_email_service(app, settings=settings, transport=transport)
    assert isinstance(service, EmailService)

    request = Request({"type": "http", "app": app})
    resolved = get_email_service(request)
    assert resolved is service

    payload = EmailMessagePayload(to=["ops@example.com"], subject="Check", text_body="Status ok")
    asyncio.run(resolved.send_email(payload))
    assert transport.call_count == 1


def test_describe_email_includes_feature_metadata(email_runtime) -> None:
    EmailConfig = email_runtime.EmailConfig
    describe_email = email_runtime.describe_email

    metadata = describe_email(EmailConfig(enabled=True, provider="console"))

    assert metadata["module"] == "email"
    assert metadata["provider"] == "console"
    assert "features" in metadata
    assert "default_headers" in metadata


def test_list_email_features_exposes_expected_flags(email_runtime) -> None:
    list_email_features = email_runtime.list_email_features
    features = list_email_features()

    assert "templated_delivery" in features
    assert isinstance(features, list)


def test_email_service_metadata_matches_describe(email_runtime) -> None:
    EmailConfig = email_runtime.EmailConfig
    EmailService = email_runtime.EmailService

    config = EmailConfig(enabled=True, provider="smtp")
    service = EmailService(config)

    assert service.metadata()["provider"] == "smtp"


def test_payload_requires_recipient_and_content(email_runtime) -> None:
    EmailMessagePayload = email_runtime.EmailMessagePayload

    payload = EmailMessagePayload(subject="Missing recipient")
    with pytest.raises(ValueError):
        payload.require_recipient()

    payload = EmailMessagePayload(subject="No content", to=["alice@example.com"])
    with pytest.raises(ValueError):
        payload.require_content()


def test_attachment_inline_and_headers(email_runtime) -> None:
    EmailAttachment = email_runtime.EmailAttachment

    attachment = EmailAttachment(
        filename="pic.png",
        content=b"data",
        content_type="image/png",
        inline=False,
        content_id="cid-1",
    )

    message = EmailMessage()
    attachment.add_to(message)

    payload = message.get_payload()
    assert isinstance(payload, list) and payload, "Attachment payload should be added"
    part = payload[-1]
    assert part.get_content_type() == "image/png"
    assert part.get_filename() == "pic.png"
    assert part.get("Content-ID") == "<cid-1>"
    assert part.get("Content-Disposition", "").startswith("attachment")


def test_send_email_disabled_short_circuits_delivery(email_runtime) -> None:
    EmailConfig = email_runtime.EmailConfig
    EmailService = email_runtime.EmailService
    EmailMessagePayload = email_runtime.EmailMessagePayload

    config = EmailConfig(enabled=False, provider="console")
    service = EmailService(config)
    payload = EmailMessagePayload(
        to=["ops@example.com"],
        subject="Disabled",
        text_body="noop",
    )

    result = asyncio.run(service.send_email(payload))

    assert result.accepted is False
    assert result.detail == "disabled"


def test_send_email_rejects_unknown_provider(email_runtime) -> None:
    EmailConfig = email_runtime.EmailConfig
    EmailService = email_runtime.EmailService
    EmailMessagePayload = email_runtime.EmailMessagePayload
    EmailDeliveryError = email_runtime.EmailDeliveryError

    config = EmailConfig(enabled=True, provider="unknown")
    service = EmailService(config)
    payload = EmailMessagePayload(
        to=["ops@example.com"],
        subject="Unknown",
        text_body="noop",
    )

    with pytest.raises(EmailDeliveryError):
        asyncio.run(service.send_email(payload))


def test_email_settings_from_env_and_dry_run_flag(email_runtime) -> None:
    EmailSettings = email_runtime.EmailSettings

    settings = EmailSettings.from_env(
        {
            "RAPIDKIT_EMAIL_ENABLED": "false",
            "RAPIDKIT_EMAIL_PROVIDER": "console",
            "RAPIDKIT_EMAIL_FROM_ADDRESS": "noreply@example.com",
            "RAPIDKIT_EMAIL_TEMPLATE_DIRECTORY": "/tmp/templates",
            "RAPIDKIT_EMAIL_TEMPLATE_AUTO_RELOAD": "1",
            "RAPIDKIT_EMAIL_TEMPLATE_STRICT": "yes",
            "RAPIDKIT_EMAIL_DRY_RUN": "true",
            "RAPIDKIT_EMAIL_DEFAULT_HEADERS": "X-One=1, X-Two=two",
        }
    )

    assert settings.enabled is False
    assert settings.provider == "console"
    assert settings.template_directory == "/tmp/templates"
    assert settings.template_auto_reload is True
    assert settings.template_strict is True
    assert settings.dry_run is True
    assert settings.default_headers == {"X-One": "1", "X-Two": "two"}

    config = settings.to_config()
    assert config.enabled is False
    assert config.metadata.get("dry_run") is True


def test_get_email_service_raises_when_unregistered(email_runtime) -> None:
    get_email_service = email_runtime.get_email_service

    class _StubState:
        email_service = None

    class _StubApp:
        state = _StubState()

    class _StubRequest:
        app = _StubApp()

    with pytest.raises(RuntimeError):
        get_email_service(_StubRequest())
