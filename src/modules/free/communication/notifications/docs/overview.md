# Notifications Module Overview

The Notifications module provides multi-channel notification delivery with email, SMS, and push
notification support. Currently focused on transactional email with SMTP transport and Jinja2
templating.

## Key Capabilities

- **Email delivery** – Transactional email via SMTP with support for Gmail, SendGrid, AWS SES, and
  custom servers.
- **Template engine** – Jinja2-powered HTML/text templates with variable substitution and layouts.
- **Multi-recipient** – Send to single or multiple recipients with CC/BCC support.
- **Attachment handling** – File attachments with automatic MIME type detection.
- **Health monitoring** – `/api/health/module/notifications` endpoint reports SMTP connectivity and
  queue status.
- **Framework integration** – FastAPI service injection and NestJS provider support.
- **Async delivery** – Non-blocking email sending with background task support.
- **Template management** – Organized template structure with base layouts and component includes.

## Module Components

- **Email Service**: SMTP-based email delivery with connection pooling
- **Template Engine**: Jinja2 template rendering with variable injection
- **Notification Queue**: Async task queue for background delivery
- **Health Checks**: SMTP connectivity and delivery status monitoring
- **Framework Adapters**: FastAPI dependencies and NestJS services

## Architecture

```
┌──────────────────────┐
│  Application Logic   │
└──────────────────────┘
         │
    ┌────────────────────────┐
    │  Email Service         │
    │  send_email()          │
    └────────────────────────┘
         │
    ┌────────────────────────┐
    │  Template Engine       │
    │  (Jinja2)              │
    └────────────────────────┘
         │
    ┌────────────────────────┐
    │  SMTP Transport        │
    │  (Gmail/SendGrid/SES)  │
    └────────────────────────┘
```

## Quick Start

### FastAPI

```python
from fastapi import FastAPI, Depends
from src.modules.free.communication.notifications.core.notifications import (
    EmailService,
    get_email_service,
)

app = FastAPI()


@app.post("/send-welcome")
async def send_welcome(
    email: str, email_service: EmailService = Depends(get_email_service)
):
    await email_service.send_email(
        to=email, template="welcome.html", context={"username": "Alice"}
    )
    return {"status": "sent"}
```

### NestJS

```typescript
import { Injectable } from '@nestjs/common';
import { EmailService } from './email.service';

@Injectable()
export class NotificationService {
  constructor(private emailService: EmailService) {}

  async sendWelcome(email: string, username: string) {
    await this.emailService.sendEmail({
      to: email,
      template: 'welcome.html',
      context: { username }
    });
  }
}
```

## Configuration

Environment variables:

```bash
# SMTP Server
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@example.com
SMTP_FROM_NAME=MyApp

# Email Settings
EMAIL_BACKEND=smtp
EMAIL_ASYNC=true
EMAIL_TEMPLATES_DIR=templates/email
EMAIL_DEFAULT_TEMPLATE=default.html
```

## Email Templates

### Template Structure

```
templates/email/
├── base.html           # Base layout
├── welcome.html        # Welcome email
├── password_reset.html # Password reset
└── components/
    ├── header.html     # Reusable header
    └── footer.html     # Reusable footer
```

### Template Example

```html
<!-- templates/email/welcome.html -->
{% extends "base.html" %}

{% block content %}
<h1>Welcome {{ username }}!</h1>
<p>Thank you for joining {{ app_name }}.</p>
<a href="{{ activation_link }}">Activate Your Account</a>
{% endblock %}
```

### Send with Template

```python
await email_service.send_email(
    to="user@example.com",
    template="welcome.html",
    subject="Welcome to MyApp",
    context={
        "username": "Alice",
        "app_name": "MyApp",
        "activation_link": "https://example.com/activate/abc123",
    },
)
```

## Multi-Recipient Support

Send to multiple recipients:

```python
await email_service.send_email(
    to=["user1@example.com", "user2@example.com"],
    cc=["admin@example.com"],
    bcc=["archive@example.com"],
    template="announcement.html",
    context={"message": "System maintenance scheduled"},
)
```

## Attachments

Send files with emails:

```python
await email_service.send_email(
    to="user@example.com",
    template="invoice.html",
    context={"invoice_id": "INV-001"},
    attachments=[
        {"filename": "invoice.pdf", "content": pdf_bytes, "mimetype": "application/pdf"}
    ],
)
```

## Async Delivery

Background email sending:

```python
from fastapi import BackgroundTasks


@app.post("/register")
async def register(email: str, background_tasks: BackgroundTasks):
    # Register user...

    # Send email in background
    background_tasks.add_task(
        email_service.send_email,
        to=email,
        template="welcome.html",
        context={"username": "Alice"},
    )

    return {"status": "registered"}
```

## SMTP Providers

### Gmail

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Not your regular password!
```

### SendGrid

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

### AWS SES

```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

## Health Monitoring

Health endpoint reports:

- SMTP server connectivity
- Template availability
- Queue depth (if using async queue)
- Recent delivery failures

```json
{
  "status": "healthy",
  "module": "notifications",
  "smtp": {
    "connected": true,
    "host": "smtp.gmail.com",
    "port": 587
  },
  "templates": {
    "loaded": 12,
    "missing": []
  },
  "queue": {
    "pending": 5,
    "failed_last_hour": 0
  }
}
```

Access health status at `/api/health/module/notifications`.

## Error Handling

Graceful failure handling:

```python
try:
    await email_service.send_email(to="user@example.com", template="welcome.html")
except Exception as exc:
    logger.error("Notification delivery failed", extra={"error": str(exc)})
```

## Future Channels

Planned notification channels:

- **SMS**: Twilio, AWS SNS integration
- **Push**: Firebase Cloud Messaging, APNs
- **In-app**: Real-time notifications via WebSocket
- **Slack/Discord**: Webhook-based team notifications

## Supported Frameworks

- **FastAPI**: Full async support with dependency injection
- **NestJS**: Injectable service with TypeScript types
- **Custom**: Direct service access for other frameworks

## Security Features

- **TLS/SSL**: Encrypted SMTP connections
- **Credential management**: Environment-based secret storage
- **Template sanitization**: XSS protection in templates
- **Rate limiting**: Prevent email abuse

## Getting Help

- **Usage Guide**: Detailed email setup and template examples
- **Advanced Guide**: Custom transports and template engines
- **Troubleshooting**: SMTP connectivity and delivery issues
- **Migration Guide**: Upgrading from previous versions

For issues and questions, visit our [GitHub repository](https://github.com/getrapidkit/core).
