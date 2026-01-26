"""FastAPI router exposing Notifications module operations."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.modules.free.communication.notifications.core.notifications import (
    Notification,
    NotificationManager,
    describe_notifications,
    get_notification_manager,
    list_notification_features,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationRequest(BaseModel):
    channel: str = Field(..., min_length=1)
    recipient: str = Field(..., min_length=3)
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    accepted: bool


@router.get("/metadata", response_model=Dict[str, Any])
async def get_notifications_metadata(
    manager: NotificationManager = Depends(get_notification_manager),
) -> Dict[str, Any]:
    """Return metadata describing configured notification providers."""

    return describe_notifications(manager)


@router.get("/features", response_model=Dict[str, Any])
async def list_features() -> Dict[str, Any]:
    """List feature flags advertised by the notifications module."""

    return {"features": list_notification_features()}


@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_notification(
    payload: NotificationRequest,
    manager: NotificationManager = Depends(get_notification_manager),
) -> NotificationResponse:
    """Dispatch a notification using the configured provider handlers."""

    payload_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    notification = Notification(**payload_data)
    accepted = await manager.send_notification(notification)
    if not accepted:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Notification delivery failed")
    return NotificationResponse(accepted=accepted)


@router.post("/verify-email", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def verify_email_transport(
    manager: NotificationManager = Depends(get_notification_manager),
) -> Dict[str, Any]:
    """Verify the configured notifications email transport."""

    service = manager.get_email_service()
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Email service not configured")

    verified = await service.verify_connection()
    if not verified:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Email verification failed")
    return {"verified": verified}


__all__ = ["router"]
