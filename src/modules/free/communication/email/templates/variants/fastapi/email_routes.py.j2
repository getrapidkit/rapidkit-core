"""FastAPI router exposing email module endpoints."""

from __future__ import annotations

import typing as t

from dataclasses import asdict, is_dataclass

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.modules.free.communication.email.email import (
    AttachmentPayload,
    EmailMessagePayload,
    EmailService,
    EmailSendResult,
    EmailDeliveryError,
    get_email_service,
    list_email_features,
)

router = APIRouter(prefix="/communication/email", tags=["email"])


class SendEmailResponse(BaseModel):
    accepted: bool
    provider: str
    message_id: str | None = Field(default=None)
    detail: str | None = Field(default=None)
    metadata: dict[str, t.Any] = Field(default_factory=dict)


class SendEmailRequest(BaseModel):
    to: list[str]
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    subject: str
    body: str | None = None
    text_body: str | None = Field(default=None, alias="textBody")
    html_body: str | None = Field(default=None, alias="htmlBody")
    reply_to: str | None = Field(default=None, alias="replyTo")
    headers: dict[str, str] = Field(default_factory=dict)
    attachments: list[AttachmentPayload] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    def to_runtime_payload(self) -> EmailMessagePayload:
        return EmailMessagePayload(
            to=self.to,
            cc=self.cc or [],
            bcc=self.bcc or [],
            subject=self.subject,
            text_body=self.text_body or self.body,
            html_body=self.html_body,
            reply_to=self.reply_to,
            headers=self.headers,
            attachments=self.attachments,
        )


class TemplatedEmailRequest(BaseModel):
    to: list[str]
    template_name: str
    context: dict[str, t.Any] = Field(default_factory=dict)
    subject: str
    text_template: str | None = Field(default=None)
    reply_to: str | None = Field(default=None)
    headers: dict[str, str] = Field(default_factory=dict)


@router.get("/metadata", response_model=dict[str, t.Any])
async def get_email_metadata(service: EmailService = Depends(get_email_service)) -> dict[str, t.Any]:
    """Return a metadata snapshot describing the email runtime."""

    return service.metadata()


@router.get("/features", response_model=dict[str, t.Any])
async def list_features() -> dict[str, t.Any]:
    """List features exposed by the email module."""

    return {"features": list_email_features()}


@router.post("/send", response_model=SendEmailResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_email(
    payload: SendEmailRequest,
    service: EmailService = Depends(get_email_service),
) -> SendEmailResponse:
    """Send a raw email message via the configured provider."""

    try:
        result = await service.send_email(payload.to_runtime_payload())
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(exc), "provider": exc.provider, "metadata": exc.metadata},
        ) from exc
    return SendEmailResponse(**_serialize_send_result(result))


@router.post("/send-templated", response_model=SendEmailResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_templated_email(
    payload: TemplatedEmailRequest,
    service: EmailService = Depends(get_email_service),
) -> SendEmailResponse:
    """Render templates and send the resulting email message."""

    try:
        result = await service.send_templated_email(
            to=payload.to,
            template_name=payload.template_name,
            context=payload.context,
            subject=payload.subject,
            text_template=payload.text_template,
            reply_to=payload.reply_to,
            headers=payload.headers,
        )
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(exc), "provider": exc.provider, "metadata": exc.metadata},
        ) from exc
    return SendEmailResponse(**_serialize_send_result(result))


@router.post("/verify", response_model=dict[str, t.Any])
async def verify_email_transport(service: EmailService = Depends(get_email_service)) -> dict[str, t.Any]:
    """Verify the underlying email transport."""

    healthy = await service.verify_connection()
    return {"verified": healthy}


@router.get("/status", response_model=dict[str, t.Any])
async def get_email_status(service: EmailService = Depends(get_email_service)) -> dict[str, t.Any]:
    """Return the runtime status for the email service."""

    return service.status()


__all__ = ["router"]


def _serialize_send_result(result: EmailSendResult) -> dict[str, t.Any]:
    """Convert runtime send results into JSON-serializable payloads."""

    if is_dataclass(result):
        return asdict(result)
    if hasattr(result, "model_dump") and callable(result.model_dump):  # type: ignore[attr-defined]
        return result.model_dump()  # type: ignore[no-any-return]
    if hasattr(result, "__dict__"):
        return dict(result.__dict__)
    return {
        "accepted": getattr(result, "accepted", False),
        "provider": getattr(result, "provider", "unknown"),
        "message_id": getattr(result, "message_id", None),
        "detail": getattr(result, "detail", None),
        "metadata": getattr(result, "metadata", {}) or {},
    }
