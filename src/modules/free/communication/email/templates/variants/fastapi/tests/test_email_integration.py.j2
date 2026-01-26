import pytest


@pytest.mark.asyncio
async def test_send_email(async_client, email_service):
    response = await async_client.post(
        "/communication/email/send",
        json={
            "to": ["test@example.com"],
            "subject": "Test Email",
            "body": "Hello from RapidKit",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["provider"] == email_service.provider
    assert isinstance(payload.get("metadata"), dict)
