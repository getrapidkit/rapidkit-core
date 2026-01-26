# pyright: reportMissingImports=false
"""Runtime primitives for the RapidKit Email module."""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
from dataclasses import dataclass, field
from email.message import EmailMessage, Message
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
)

from pydantic import BaseModel, EmailStr, Field

OPTIONAL_IMPORT_ERRORS = (ImportError, ModuleNotFoundError, RuntimeError)
MIN_SMTP_RESPONSE_FIELDS = 2

aiosmtplib: Any | None

try:  # Optional dependency for SMTP support
    aiosmtplib = importlib.import_module("aiosmtplib")
except OPTIONAL_IMPORT_ERRORS:  # pragma: no cover - optional dependency not installed
    aiosmtplib = None
    SMTP_ERRORS: tuple[type[Exception], ...] = (asyncio.TimeoutError, OSError)
else:  # pragma: no cover - executed only when dependency available
    SMTP_ERRORS = (
        aiosmtplib.errors.SMTPException,
        asyncio.TimeoutError,
        OSError,
    )

try:  # Optional dependency for templating support
    Jinja2Environment: Any
    FileSystemLoader: Any
    TemplateNotFound: Any
    select_autoescape: Any
    from jinja2 import (
        Environment as Jinja2Environment,
        FileSystemLoader,
        TemplateNotFound,
        select_autoescape,
    )
except OPTIONAL_IMPORT_ERRORS:  # pragma: no cover - optional dependency not installed
    Jinja2Environment = None
    FileSystemLoader = None
    TemplateNotFound = None
    select_autoescape = None

if TYPE_CHECKING:  # pragma: no cover - typing only
    from jinja2 import Environment as _JinjaEnvironment
else:  # pragma: no cover - runtime fallback when jinja2 missing
    _JinjaEnvironment = Any

try:  # FastAPI is optional for consumers that only need the core service
    FastAPI: Any
    Request: Any
    from fastapi import FastAPI, Request
except OPTIONAL_IMPORT_ERRORS:  # pragma: no cover - FastAPI optional
    FastAPI = None
    Request = None

LOGGER = logging.getLogger("communication.email")

TransportCallable = Callable[[EmailMessage], Awaitable[Optional[str]]]

_FEATURE_FLAGS: tuple[str, ...] = (
    "smtp_transport",
    "console_transport",
    "templated_delivery",
    "default_headers",
    "dry_run_mode",
    "metadata_reporting",
)


@dataclass(slots=True)
class SMTPSettings:
    """SMTP provider configuration."""

    host: str = "localhost"
    port: int = 1025
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    timeout_seconds: float = 30.0

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SMTPSettings":
        defaults = cls()
        return cls(
            host=str(payload.get("host", defaults.host)),
            port=int(payload.get("port", defaults.port)),
            username=payload.get("username") or None,
            password=payload.get("password") or None,
            use_tls=bool(payload.get("use_tls", defaults.use_tls)),
            timeout_seconds=float(payload.get("timeout_seconds", defaults.timeout_seconds)),
        )


@dataclass(slots=True)
class TemplateSettings:
    """Controls template discovery and caching behaviour."""

    directory: Optional[Path] = None
    auto_reload: bool = False
    strict: bool = False

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TemplateSettings":
        defaults = cls()
        directory = payload.get("directory")
        path = Path(directory).expanduser() if directory else None
        return cls(
            directory=path,
            auto_reload=bool(payload.get("auto_reload", defaults.auto_reload)),
            strict=bool(payload.get("strict", defaults.strict)),
        )


@dataclass(slots=True)
class EmailConfig:
    """Resolved runtime configuration for the email service."""

    enabled: bool = True
    provider: str = "smtp"
    from_email: str = "noreply@rapidkit.local"
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    default_headers: MutableMapping[str, str] = field(default_factory=dict)
    metadata: MutableMapping[str, Any] = field(default_factory=dict)
    smtp: SMTPSettings = field(default_factory=SMTPSettings)
    template: TemplateSettings = field(default_factory=TemplateSettings)

    def sender_header(self) -> str:
        if self.from_name:
            return f"{self.from_name} <{self.from_email}>"
        return self.from_email

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "EmailConfig":
        defaults = cls()
        smtp_payload = payload.get("smtp", {})
        template_payload = payload.get("template", {})
        return cls(
            enabled=bool(payload.get("enabled", defaults.enabled)),
            provider=str(payload.get("provider", defaults.provider)),
            from_email=str(payload.get("from_email", defaults.from_email)),
            from_name=payload.get("from_name") or None,
            reply_to=payload.get("reply_to") or None,
            default_headers=dict(payload.get("default_headers", {})),
            metadata=dict(payload.get("metadata", {})),
            smtp=SMTPSettings.from_mapping(
                smtp_payload if isinstance(smtp_payload, Mapping) else {}
            ),
            template=TemplateSettings.from_mapping(
                template_payload if isinstance(template_payload, Mapping) else {}
            ),
        )


class AttachmentPayload(BaseModel):
    """Attachment payload validated before adding to email messages."""

    filename: str
    content: bytes
    content_type: str = Field(default="application/octet-stream")
    inline: bool = Field(default=False)
    content_id: Optional[str] = Field(default=None)

    def to_runtime(self) -> "EmailAttachment":
        return EmailAttachment(
            filename=self.filename,
            content=self.content,
            content_type=self.content_type,
            inline=self.inline,
            content_id=self.content_id,
        )


class EmailMessagePayload(BaseModel):
    """Structured email payload for runtime delivery."""

    to: list[EmailStr] = Field(default_factory=list)
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    subject: str
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    attachments: list[AttachmentPayload] = Field(default_factory=list)

    model_config = {
        "str_strip_whitespace": True,
        "use_enum_values": True,
    }

    def require_recipient(self) -> None:
        if not (self.to or self.cc or self.bcc):
            raise ValueError("At least one recipient must be provided")

    def require_content(self) -> None:
        if not (self.text_body or self.html_body):
            raise ValueError("text_body or html_body must be supplied")

    def attachments_as_runtime(self) -> Sequence["EmailAttachment"]:
        return tuple(attachment.to_runtime() for attachment in self.attachments)


@dataclass(slots=True)
class EmailAttachment:
    """Binary attachment to include with a message."""

    filename: str
    content: bytes
    content_type: str
    inline: bool = False
    content_id: Optional[str] = None

    def add_to(self, message: EmailMessage) -> None:
        maintype, subtype = self._split_content_type()
        message.add_attachment(
            self.content,
            maintype=maintype,
            subtype=subtype,
            filename=self.filename,
        )
        payload = message.get_payload()
        if isinstance(payload, list) and payload:
            part = payload[-1]
            if isinstance(part, Message):
                if self.inline:
                    part.add_header("Content-Disposition", "inline", filename=self.filename)
                if self.content_id:
                    part.add_header("Content-ID", f"<{self.content_id}>")

    def _split_content_type(self) -> tuple[str, str]:
        maintype, _, subtype = self.content_type.partition("/")
        maintype = maintype or "application"
        subtype = subtype or "octet-stream"
        return maintype, subtype


@dataclass(slots=True)
class EmailSendResult:
    """Summary of a delivery attempt."""

    accepted: bool
    provider: str
    message_id: Optional[str] = None
    detail: Optional[str] = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)


class EmailDeliveryError(RuntimeError):
    """Raised when delivery fails in a non-recoverable way."""

    def __init__(
        self, message: str, *, provider: str, metadata: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.metadata = dict(metadata or {})


class EmailTemplateRenderer:
    """Jinja-backed template renderer for HTML and text payloads."""

    def __init__(self, settings: TemplateSettings) -> None:
        self.settings = settings
        self._environment: Optional[_JinjaEnvironment] = None
        if settings.directory:
            self.configure(settings.directory, auto_reload=settings.auto_reload)

    def configure(self, directory: Path, *, auto_reload: Optional[bool] = None) -> None:
        if Jinja2Environment is None or FileSystemLoader is None or select_autoescape is None:
            raise RuntimeError(
                "jinja2 is required for template rendering. Install it with 'pip install jinja2'."
            )
        loader = FileSystemLoader(str(directory))
        self._environment = Jinja2Environment(
            loader=loader,
            autoescape=select_autoescape(enabled_extensions=("html", "xml"), default=True),
            auto_reload=self.settings.auto_reload if auto_reload is None else auto_reload,
            enable_async=False,
        )
        self.settings.directory = directory

    def render(self, template_name: str, context: Mapping[str, Any]) -> str:
        if self._environment is None:
            raise RuntimeError("Template environment not configured")
        try:
            template = self._environment.get_template(template_name)
        except TemplateNotFound as exc:  # pragma: no cover - simple pass through
            if self.settings.strict:
                raise RuntimeError(f"Template '{template_name}' not found") from exc
            LOGGER.warning("Template '%s' not found; returning empty string", template_name)
            return ""
        return template.render(**context)


class EmailService:
    """Asynchronous email delivery service with pluggable transports."""

    def __init__(
        self,
        config: EmailConfig,
        *,
        transport: Optional[TransportCallable] = None,
        template_renderer: Optional[EmailTemplateRenderer] = None,
    ) -> None:
        self.config = config
        self._transport = transport
        self._renderer = template_renderer or EmailTemplateRenderer(config.template)
        self._lock = asyncio.Lock()

    @property
    def provider(self) -> str:
        return self.config.provider.lower()

    def list_features(self) -> list[str]:
        """Return the feature flags supported by the email runtime."""

        return list_email_features()

    def set_template_directory(
        self, directory: Path, *, auto_reload: Optional[bool] = None
    ) -> None:
        self._renderer.configure(directory, auto_reload=auto_reload)

    async def send_email(self, payload: EmailMessagePayload) -> EmailSendResult:
        payload.require_recipient()
        payload.require_content()

        message = self._build_message(payload)

        if not self.config.enabled:
            LOGGER.info("Email service disabled; skipping delivery")
            return EmailSendResult(accepted=False, provider=self.provider, detail="disabled")

        async with self._lock:
            if self._transport is not None:
                message_id = await self._transport(message)
                return EmailSendResult(
                    accepted=True,
                    provider=self.provider,
                    message_id=message_id,
                )
            if self.provider == "smtp":
                return await self._send_via_smtp(message)
            if self.provider == "console":
                return self._send_via_console(message)
            raise EmailDeliveryError(
                f"Unsupported email provider '{self.config.provider}'",
                provider=self.provider,
            )

    async def send_templated_email(
        self,
        to: Iterable[str],
        *,
        template_name: str,
        context: Mapping[str, Any],
        subject: str,
        text_template: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> EmailSendResult:
        html = self._renderer.render(template_name, context)
        text: Optional[str] = None
        if text_template:
            text = self._renderer.render(text_template, context)
        payload = EmailMessagePayload(
            to=list(to),
            subject=subject,
            html_body=html,
            text_body=text,
            reply_to=reply_to,
            headers=dict(headers or {}),
        )
        return await self.send_email(payload)

    async def verify_connection(self) -> bool:
        if self.provider == "console":
            return True
        if self.provider == "smtp":
            if aiosmtplib is None:
                raise EmailDeliveryError(
                    "aiosmtplib is required for SMTP verification",
                    provider=self.provider,
                )
            config = self.config.smtp
            try:
                await aiosmtplib.SMTP(
                    hostname=config.host,
                    port=config.port,
                    username=config.username,
                    password=config.password,
                    timeout=config.timeout_seconds,
                    start_tls=config.use_tls,
                ).quit()
                return True
            except Exception as exc:  # pragma: no cover - network interactions
                LOGGER.exception("SMTP verification failed", exc_info=exc)
                return False
        return False

    def status(self) -> Mapping[str, Any]:
        return {
            "enabled": self.config.enabled,
            "provider": self.provider,
            "features": self.list_features(),
            "templates": {
                "directory": (
                    str(self.config.template.directory) if self.config.template.directory else None
                ),
                "auto_reload": self.config.template.auto_reload,
                "strict": self.config.template.strict,
            },
            "default_headers": dict(self.config.default_headers),
            "metadata": dict(self.config.metadata),
        }

    def metadata(self) -> Dict[str, Any]:
        """Return a metadata snapshot describing the runtime."""

        return describe_email(self.config)

    def _build_message(self, payload: EmailMessagePayload) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = payload.subject
        message["From"] = self.config.sender_header()
        message["To"] = ", ".join(str(address) for address in payload.to)
        if payload.cc:
            message["Cc"] = ", ".join(str(address) for address in payload.cc)
        if payload.bcc:
            message["Bcc"] = ", ".join(str(address) for address in payload.bcc)
        reply_to = payload.reply_to or self.config.reply_to
        if reply_to:
            message["Reply-To"] = str(reply_to)

        combined_headers: Dict[str, str] = {**self.config.default_headers, **payload.headers}
        for header, value in combined_headers.items():
            message[header] = value

        text_content = payload.text_body or payload.html_body or ""
        message.set_content(text_content)
        if payload.html_body:
            message.add_alternative(payload.html_body, subtype="html")

        for attachment in payload.attachments_as_runtime():
            attachment.add_to(message)
        return message

    async def _send_via_smtp(self, message: EmailMessage) -> EmailSendResult:
        if aiosmtplib is None:
            raise EmailDeliveryError(
                "aiosmtplib is required for SMTP delivery",
                provider=self.provider,
            )
        config = self.config.smtp
        try:
            response = await aiosmtplib.send(
                message,
                hostname=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
                timeout=config.timeout_seconds,
                start_tls=config.use_tls,
            )
        except SMTP_ERRORS as exc:
            LOGGER.exception("SMTP delivery failed", exc_info=exc)
            raise EmailDeliveryError(
                "SMTP transport failed",
                provider=self.provider,
                metadata={"error": str(exc)},
            ) from exc

        message_id = None
        detail = None
        if isinstance(response, tuple) and len(response) >= MIN_SMTP_RESPONSE_FIELDS:
            code, info = response[0], response[1]
            detail = f"{code} {info}"
        elif hasattr(response, "message"):
            detail = str(response.message)
        return EmailSendResult(
            accepted=True, provider=self.provider, message_id=message_id, detail=detail
        )

    def _send_via_console(self, message: EmailMessage) -> EmailSendResult:
        LOGGER.info("Console email delivery\n%s", message.as_string())
        return EmailSendResult(accepted=True, provider=self.provider, detail="console")


class EmailSettings(BaseModel):
    """Declarative settings surface for email configuration."""

    enabled: bool = True
    provider: str = Field(default="smtp", pattern=r"^[a-z0-9_-]+$")
    from_email: EmailStr = Field(default="noreply@example.com")
    from_name: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    smtp_host: str = Field(default="localhost")
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = False
    smtp_timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0)
    template_directory: Optional[str] = None
    template_auto_reload: bool = False
    template_strict: bool = False
    dry_run: bool = False
    default_headers: Dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "EmailSettings":
        env = env or os.environ
        data = {
            "enabled": _as_bool(env.get("RAPIDKIT_EMAIL_ENABLED"), True),
            "provider": env.get("RAPIDKIT_EMAIL_PROVIDER", cls.model_fields["provider"].default),
            "from_email": env.get(
                "RAPIDKIT_EMAIL_FROM_ADDRESS", cls.model_fields["from_email"].default
            ),
            "from_name": env.get("RAPIDKIT_EMAIL_FROM_NAME"),
            "reply_to": env.get("RAPIDKIT_EMAIL_REPLY_TO"),
            "smtp_host": env.get("RAPIDKIT_EMAIL_SMTP_HOST", cls.model_fields["smtp_host"].default),
            "smtp_port": env.get("RAPIDKIT_EMAIL_SMTP_PORT"),
            "smtp_username": env.get("RAPIDKIT_EMAIL_SMTP_USERNAME"),
            "smtp_password": env.get("RAPIDKIT_EMAIL_SMTP_PASSWORD"),
            "smtp_use_tls": env.get("RAPIDKIT_EMAIL_SMTP_USE_TLS"),
            "smtp_timeout_seconds": env.get("RAPIDKIT_EMAIL_SMTP_TIMEOUT"),
            "template_directory": env.get("RAPIDKIT_EMAIL_TEMPLATE_DIRECTORY"),
            "template_auto_reload": env.get("RAPIDKIT_EMAIL_TEMPLATE_AUTO_RELOAD"),
            "template_strict": env.get("RAPIDKIT_EMAIL_TEMPLATE_STRICT"),
            "dry_run": env.get("RAPIDKIT_EMAIL_DRY_RUN"),
        }
        headers_raw = env.get("RAPIDKIT_EMAIL_DEFAULT_HEADERS")
        if headers_raw:
            pairs = [item.strip() for item in headers_raw.split(",") if item.strip()]
            headers: Dict[str, str] = {}
            for pair in pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    headers[key.strip()] = value.strip()
            data["default_headers"] = headers
        return cls(**{k: v for k, v in data.items() if v is not None})

    def to_config(self) -> EmailConfig:
        smtp_payload = {
            "host": self.smtp_host,
            "port": self.smtp_port,
            "username": self.smtp_username,
            "password": self.smtp_password,
            "use_tls": self.smtp_use_tls,
            "timeout_seconds": self.smtp_timeout_seconds,
        }
        template_payload = {
            "directory": self.template_directory,
            "auto_reload": self.template_auto_reload,
            "strict": self.template_strict,
        }
        config = EmailConfig.from_mapping(
            {
                "enabled": self.enabled and not self.dry_run,
                "provider": self.provider,
                "from_email": str(self.from_email),
                "from_name": self.from_name,
                "reply_to": str(self.reply_to) if self.reply_to else None,
                "default_headers": self.default_headers,
                "smtp": smtp_payload,
                "template": template_payload,
            }
        )
        if self.dry_run:
            config.metadata.setdefault("dry_run", True)
        return config


def register_email_service(
    app: Any,
    *,
    settings: Optional[EmailSettings] = None,
    transport: Optional[TransportCallable] = None,
) -> EmailService:
    """Attach the email service to a FastAPI application instance."""

    if FastAPI is not None and isinstance(app, FastAPI):
        fastapi_app = app
    elif FastAPI is None:
        raise RuntimeError("FastAPI is required to register the email service")
    else:
        raise TypeError("register_email_service expects a FastAPI application instance")

    settings = settings or EmailSettings.from_env()
    config = settings.to_config()
    service = EmailService(config, transport=transport)

    if settings.template_directory:
        service.set_template_directory(Path(settings.template_directory).expanduser())

    fastapi_app.state.email_service = service
    fastapi_app.state.email_settings = settings
    LOGGER.info("Email service registered", extra={"provider": service.provider})
    return service


def get_email_service(request: Any) -> EmailService:
    """FastAPI dependency that returns the configured email service."""

    if Request is not None and isinstance(request, Request):
        service = getattr(request.app.state, "email_service", None)
    else:
        service = getattr(getattr(request, "app", None), "state", object())
        service = getattr(service, "email_service", None)
    if not isinstance(service, EmailService):
        raise RuntimeError(
            "Email service has not been registered. Call register_email_service() during startup."
        )
    return service


def describe_email(
    config: EmailConfig | EmailSettings | Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return a normalized metadata payload describing the email runtime."""

    resolved: EmailConfig
    if config is None:
        resolved = EmailSettings.from_env().to_config()
    elif isinstance(config, EmailConfig):
        resolved = config
    elif isinstance(config, EmailSettings):
        resolved = config.to_config()
    elif isinstance(config, Mapping):
        resolved = EmailConfig.from_mapping(config)
    else:  # pragma: no cover - defensive branch
        raise TypeError("Unsupported configuration payload for describe_email")

    template_directory = (
        str(resolved.template.directory) if resolved.template.directory is not None else None
    )

    return {
        "module": "email",
        "enabled": resolved.enabled,
        "provider": resolved.provider,
        "from_email": resolved.from_email,
        "from_name": resolved.from_name,
        "reply_to": resolved.reply_to,
        "supports_templates": bool(resolved.template.directory),
        "template_directory": template_directory,
        "template_auto_reload": resolved.template.auto_reload,
        "template_strict": resolved.template.strict,
        "supports_smtp": resolved.provider.lower() == "smtp",
        "smtp": {
            "host": resolved.smtp.host,
            "port": resolved.smtp.port,
            "username": resolved.smtp.username,
            "timeout_seconds": resolved.smtp.timeout_seconds,
            "use_tls": resolved.smtp.use_tls,
        },
        "metadata": dict(resolved.metadata),
        "default_headers": dict(resolved.default_headers),
        "features": list_email_features(),
    }


def list_email_features() -> list[str]:
    """Enumerate the capabilities advertised by the email module."""

    return list(_FEATURE_FLAGS)


def get_email_metadata(
    config: EmailConfig | EmailSettings | Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Convenience wrapper mirroring the runtime metadata signature."""

    return describe_email(config)


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


__all__ = [
    "AttachmentPayload",
    "EmailAttachment",
    "EmailConfig",
    "EmailDeliveryError",
    "EmailMessagePayload",
    "EmailSendResult",
    "EmailService",
    "EmailSettings",
    "EmailTemplateRenderer",
    "SMTPSettings",
    "TemplateSettings",
    "describe_email",
    "get_email_metadata",
    "list_email_features",
    "get_email_service",
    "register_email_service",
]
