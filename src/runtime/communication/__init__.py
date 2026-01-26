"""Runtime primitives for communication modules."""

from .email import (
    EmailAttachment,
    EmailConfig,
    EmailDeliveryError,
    EmailMessagePayload,
    EmailSendResult,
    EmailService,
    SMTPSettings,
    TemplateSettings,
    get_email_service,
    register_email_service,
)

__all__ = [
    "EmailAttachment",
    "EmailConfig",
    "EmailDeliveryError",
    "EmailMessagePayload",
    "EmailSendResult",
    "EmailService",
    "SMTPSettings",
    "TemplateSettings",
    "register_email_service",
    "get_email_service",
]
