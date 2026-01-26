# Notifications Module - Usage Guide

Quick start guide for sending emails and managing notifications with the RapidKit notifications
module.

## Installation

```bash
rapidkit add module notifications
```

This generates:

- **FastAPI**: `src/modules/free/communication/notifications/core/notifications.py` with
  `EmailService` and `NotificationManager`
- **NestJS**: `src/modules/free/communication/notifications/notifications.service.ts` with
  injectable services

## FastAPI Quick Start

### Basic Setup

```python
from fastapi import FastAPI
from src.modules.free.communication.notifications.core.notifications import (
    register_notifications,
    EmailConfig,
    NotificationManager,
)

app = FastAPI()

# Configure SMTP
email_config = EmailConfig(
    host="smtp.sendgrid.net",
    port=587,
    username="apikey",
    password="SG.your-api-key",
    from_email="noreply@yourapp.com",
)

# Register notifications with the app
notification_manager = register_notifications(app, email_config)
```

### Sending Simple Email

```python
from src.modules.free.communication.notifications.core.notifications import (
    EmailMessage,
    NotificationType,
    Notification,
)


@app.post("/send-welcome")
async def send_welcome_email(email: str):
    notification = Notification(
        type=NotificationType.EMAIL,
        recipient=email,
        title="Welcome to Our App",
        body="<h1>Welcome!</h1><p>Thanks for signing up.</p>",
    )

    manager = await get_notification_manager(app)
    success = await manager.send_notification(notification)

    return {"sent": success}
```

### Sending Email with Template

First, create an email template at `templates/emails/welcome.hbs`:

```handlebars
<h1>Welcome, {{name}}!</h1>
<p>Your account has been created.</p>
<p>
  <a href="{{confirm_url}}">Confirm your email</a>
</p>
```

Then send:

```python
from src.modules.free.communication.notifications.core.notifications import (
    EmailNotification,
    NotificationType,
)


@app.post("/send-welcome-template")
async def send_welcome_template(email: str, name: str):
    manager = await get_notification_manager(app)

    # Set template directory (do this once during startup)
    email_service = manager.emailService
    email_service.set_template_directory("templates/emails")

    notification = EmailNotification(
        type=NotificationType.EMAIL,
        recipient=email,
        title="Welcome to Our App",
        body="",
        template="welcome",
        context={
            "name": name,
            "confirm_url": f"https://yourapp.com/confirm?email={email}",
        },
    )

    return await manager.send_notification(notification)
```

### Sending to Multiple Recipients

```python
from src.modules.free.communication.notifications.core.notifications import EmailMessage

email_service = manager.emailService

message = EmailMessage(
    to=["user1@example.com", "user2@example.com"],
    cc=["admin@example.com"],
    subject="Project Update",
    html="<p>Here's what's new...</p>",
)

success = await email_service.send_email(message)
```

## NestJS Quick Start

### Module Setup

```typescript
import { Module } from '@nestjs/common';
import { EmailService, NotificationManager } from './notifications.service';

@Module({
  providers: [
    {
      provide: 'EMAIL_CONFIG',
      useValue: {
        host: 'smtp.sendgrid.net',
        port: 587,
        username: 'apikey',
        password: process.env.SENDGRID_API_KEY,
        from_email: 'noreply@yourapp.com',
      },
    },
    {
      provide: 'CACHE_ENABLED',
      useValue: true,
    },
    EmailService,
    NotificationManager,
  ],
  exports: [EmailService, NotificationManager],
})
export class NotificationsModule {}
```

### Using in a Service

```typescript
import { Injectable } from '@nestjs/common';
import { EmailService, NotificationType } from './notifications.service';

@Injectable()
export class UserService {
  constructor(private emailService: EmailService) {}

  async sendWelcomeEmail(email: string, name: string): Promise<boolean> {
    return this.emailService.sendTemplatedEmail(
      [email],
      'welcome',
      { name, confirm_url: `https://yourapp.com/confirm?email=${email}` },
      'Welcome to Our App'
    );
  }
}
```

### Health Check Integration

```typescript
import { Controller, Get } from '@nestjs/common';
import { HealthCheck, HealthCheckService, HttpHealthIndicator } from '@nestjs/terminus';
import { EmailService } from './notifications.service';

@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private emailService: EmailService
  ) {}

  @Get('notifications')
  @HealthCheck()
  async check() {
    return this.health.check([
      async () => {
        const isConnected = await this.emailService.verifyConnection();
        return {
          notifications: {
            status: isConnected ? 'up' : 'down',
          },
        };
      },
    ]);
  }
}
```

## Health Check Endpoint

Both FastAPI and NestJS variants expose a health check endpoint:

```bash
curl http://localhost:8000/health/notifications
```

Response:

```json
{
  "status": "ok",
  "module": "notifications",
  "version": "0.1.0",
  "services": {
    "email": "connected",
    "push": "not_configured",
    "sms": "not_configured"
  },
  "checked_at": "2025-01-15T10:30:45.123Z"
}
```

## Common Patterns

### Startup Tasks

```python
@app.on_event("startup")
async def startup():
    manager = await get_notification_manager(app)
    email_service = manager.emailService

    # Set template directory
    email_service.set_template_directory("templates/emails")

    # Verify SMTP connection
    connected = await email_service.verifyConnection()
    if not connected:
        raise RuntimeError("Failed to connect to SMTP server")
```

### Error Handling

```python
async def send_notification_safe(manager, notification):
    try:
        success = await manager.send_notification(notification)
        if not success:
            logger.warning(f"Notification delivery failed for {notification.recipient}")
        return success
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}", exc_info=True)
        return False
```

### Background Tasks

```python
from celery import Celery

celery = Celery(__name__)


@celery.task
def send_email_async(recipient: str, subject: str, html: str):
    # This would run in a worker process
    pass
```

## Environment Variables

Configure via environment:

```bash
export RAPIDKIT_NOTIFICATIONS_SMTP_HOST=smtp.sendgrid.net
export RAPIDKIT_NOTIFICATIONS_SMTP_PORT=587
export RAPIDKIT_NOTIFICATIONS_SMTP_USERNAME=apikey
export RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD=SG.your-api-key
export RAPIDKIT_NOTIFICATIONS_SMTP_FROM=noreply@yourapp.com
export RAPIDKIT_NOTIFICATIONS_ENABLE_TEMPLATE_CACHING=true
```

Then load in your app:

```python
import os
from src.modules.free.communication.notifications.core.notifications import EmailConfig

config = EmailConfig(
    host=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_HOST"),
    port=int(os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_PORT", "587")),
    username=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_USERNAME"),
    password=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD"),
    from_email=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_FROM"),
)
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_send_email():
    config = EmailConfig(...)
    service = EmailService(config)

    message = EmailMessage(to=["test@example.com"], subject="Test", html="<p>Test</p>")

    result = await service.send_email(message)
    assert result is True
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_notification_manager():
    manager = NotificationManager()
    # Setup and test
    pass
```

## Next Steps

- See **advanced.md** for custom email providers, retry logic, and batch sending
- See **troubleshooting.md** for common issues and debugging
- See **migration.md** for upgrading between versions
