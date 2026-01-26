from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field
from starlette.requests import Request


def _install_email_runtime_stub():
    """Provide a lightweight vendor stub so tests do not need packaged payloads."""

    import sys
    from dataclasses import dataclass, field
    from types import ModuleType
    from typing import Any, Dict

    module_name = "src.modules.free.communication.email.email"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing

    module = ModuleType(module_name)

    class AttachmentPayload(BaseModel):
        filename: str
        content: bytes | str | None = None
        content_type: str = Field(default="application/octet-stream", alias="contentType")
        inline: bool = False
        content_id: str | None = Field(default=None, alias="contentId")

        model_config = {"populate_by_name": True}

    class EmailMessagePayload(BaseModel):
        to: list[str]
        cc: list[str] = Field(default_factory=list)
        bcc: list[str] = Field(default_factory=list)
        subject: str
        html_body: str | None = Field(default=None, alias="htmlBody")
        text_body: str | None = Field(default=None, alias="textBody")
        reply_to: str | None = Field(default=None, alias="replyTo")
        headers: Dict[str, str] = Field(default_factory=dict)
        attachments: list[AttachmentPayload] = Field(default_factory=list)

        model_config = {"populate_by_name": True}

    @dataclass(slots=True)
    class EmailSendResult:
        accepted: bool
        provider: str
        message_id: str | None = None
        detail: str | None = None
        metadata: Dict[str, Any] = field(default_factory=dict)

    class EmailDeliveryError(RuntimeError):
        def __init__(self, message: str, *, provider: str, metadata: Dict[str, Any] | None = None) -> None:
            super().__init__(message)
            self.provider = provider
            self.metadata = dict(metadata or {})

    class EmailService:
        def __init__(self) -> None:
            self._messages: list[Dict[str, Any]] = []
            self.provider = "stub"

        async def send_email(self, payload: EmailMessagePayload) -> EmailSendResult:
            self._messages.append(payload.model_dump())
            return EmailSendResult(
                accepted=True,
                provider="stub",
                message_id=f"stub-{len(self._messages)}",
                metadata={"deliveries": len(self._messages)},
            )

        async def send_templated_email(
            self,
            *,
            to: Iterable[str],
            template_name: str,
            context: Dict[str, Any],
            subject: str,
            text_template: str | None = None,
            reply_to: str | None = None,
            headers: Dict[str, str] | None = None,
        ) -> EmailSendResult:
            payload = EmailMessagePayload(
                to=list(to),
                subject=subject,
                text_body=text_template or "rendered",
                html_body=context.get("html") if context else None,
                reply_to=reply_to,
                headers=dict(headers or {}),
            )
            return await self.send_email(payload)

        async def verify_connection(self) -> bool:
            return True

        def status(self) -> Dict[str, Any]:
            return {"provider": "stub", "deliveries": len(self._messages)}

        def metadata(self) -> Dict[str, Any]:
            return {"provider": "stub", "features": list_email_features()}

    stub_service = EmailService()

    def list_email_features() -> list[str]:
        return ["raw_delivery", "templated_delivery", "status"]

    def get_email_service(request: Any = None) -> EmailService:  # noqa: ARG001 - parity with real runtime
        return stub_service

    module.AttachmentPayload = AttachmentPayload
    module.EmailMessagePayload = EmailMessagePayload
    module.EmailSendResult = EmailSendResult
    module.EmailDeliveryError = EmailDeliveryError
    module.EmailService = EmailService
    module.list_email_features = list_email_features
    module.get_email_service = get_email_service

    sys.modules[module_name] = module
    return module


_install_email_runtime_stub()

from src.modules.free.communication.email.email import EmailService, get_email_service
from src.modules.free.communication.email.routers.email import router as email_router


@pytest.fixture(scope="session")
def email_app() -> FastAPI:
    """Spin up a lightweight FastAPI app that exposes the email routes."""

    app = FastAPI()
    app.include_router(email_router)
    return app


@pytest.fixture(scope="session")
def email_service() -> EmailService:
    """Provide the shared stub email service."""

    return get_email_service()


@pytest_asyncio.fixture()
async def async_client(email_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Provide an AsyncClient bound to the email test application."""

    transport = ASGITransport(app=email_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
