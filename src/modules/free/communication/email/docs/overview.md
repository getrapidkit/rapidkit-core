# Email Module Overview

The Email module provides production-ready transactional email delivery with SMTP, Mailgun, and
SendGrid transports. Built on Jinja2 templating with multi-framework support for FastAPI and NestJS.

## Key Capabilities

- **Multiple transports** – SMTP, Mailgun API, SendGrid API with automatic fallback support.
- **Template engine** – Jinja2-powered HTML/text templates with layouts, includes, and variable
  substitution.
- **Multi-recipient** – Send to single or multiple recipients with CC/BCC support.
- **Attachment handling** – Files and inline images with automatic MIME type detection.
- **Health monitoring** – `/api/health/module/email` endpoint reports transport connectivity and
  queue status.
- **Framework integration** – FastAPI dependency injection and NestJS provider support.
- **Async delivery** – Non-blocking email sending with connection pooling.
- **Testing utilities** – Mock email backend for development and testing.

## Module Components

- **Email Service**: Core email delivery with transport abstraction
- **Transports**: SMTP, Mailgun, SendGrid implementations
- **Template Engine**: Jinja2 rendering with layout inheritance
- **Health Checks**: Transport connectivity and delivery monitoring
- **Framework Adapters**: FastAPI dependencies and NestJS services
- **Testing Tools**: Mock backend for unit testing

## Architecture

```
┌──────────────────────┐
│  Application Code    │
└──────────────────────┘
         │
    ┌────────────────────────┐
    │  Email Service         │
    │  send()                │
    └────────────────────────┘
         │
    ┌────────────────────────────────┐
    │  Transport Layer               │
    ├───────────┬──────────┬─────────┤
    │  SMTP     │ Mailgun  │SendGrid│
    └───────────┴──────────┴─────────┘
         │
    ┌────────────────────────┐
    │  Template Engine       │
    │  (Jinja2)              │
    └────────────────────────┘
```

## Quick Start

### FastAPI

```python
from fastapi import FastAPI, Depends
from src.modules.free.communication.email import EmailService, get_email_service

app = FastAPI()


@app.post("/send")
async def send_email(
    recipient: str, email_service: EmailService = Depends(get_email_service)
):
    await email_service.send(
        to=recipient,
        subject="Welcome to MyApp",
        template="welcome.html",
        context={"username": "Alice", "app_name": "MyApp"},
    )
    return {"status": "sent"}
```

### NestJS

```typescript
import { Injectable } from '@nestjs/common';
import { EmailService } from '@rapidkit/email';

@Injectable()
export class NotificationService {
  constructor(private emailService: EmailService) {}

  async sendWelcome(email: string, username: string) {
    await this.emailService.send({
      to: email,
      subject: 'Welcome!',
      template: 'welcome.html',
      context: { username }
    });
  }
}
```

## Configuration

Environment variables:

```bash
# Transport Selection
EMAIL_TRANSPORT=smtp  # smtp | mailgun | sendgrid

# SMTP Transport
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@example.com
SMTP_FROM_NAME=MyApp

# Mailgun Transport
MAILGUN_API_KEY=key-xxx
MAILGUN_DOMAIN=mg.example.com
MAILGUN_FROM=noreply@mg.example.com

# SendGrid Transport
SENDGRID_API_KEY=SG.xxx
SENDGRID_FROM=noreply@example.com

# Template Settings
EMAIL_TEMPLATES_DIR=templates/email
EMAIL_DEFAULT_TEMPLATE=default.html
```

## Email Templates

### Template Structure

```
templates/email/
├── layouts/
│   └── base.html           # Base layout
├── welcome.html            # Welcome email
├── password_reset.html     # Password reset
├── order_confirmation.html # Order notification
└── components/
    ├── header.html         # Reusable header
    ├── footer.html         # Reusable footer
    └── button.html         # Reusable button
```

### Template Example

```html
<!-- templates/email/welcome.html -->
{% extends "layouts/base.html" %}

{% block content %}
<div class="container">
  <h1>Welcome {{ username }}!</h1>
  <p>Thanks for joining {{ app_name }}.</p>

  {% include "components/button.html" with
      text="Activate Account",
      url=activation_link
  %}
</div>
{% endblock %}
```

### Send with Template

```python
await email_service.send(
    to="user@example.com",
    subject="Welcome to MyApp",
    template="welcome.html",
    context={
        "username": "Alice",
        "app_name": "MyApp",
        "activation_link": "https://example.com/activate/abc123",
    },
)
```

## Transport Options

### SMTP Transport

Direct SMTP connection:

```python
from src.modules.free.communication.email.transports import SMTPTransport

transport = SMTPTransport(
    host="smtp.gmail.com",
    port=587,
    username="noreply@example.com",
    password="app-password",
)
```

### Mailgun Transport

API-based delivery via Mailgun:

```python
from src.modules.free.communication.email.transports import MailgunTransport

transport = MailgunTransport(api_key="key-xxx", domain="mg.example.com")
```

### SendGrid Transport

API-based delivery via SendGrid:

```python
from src.modules.free.communication.email.transports import SendGridTransport

transport = SendGridTransport(api_key="SG.xxx")
```

## Multi-Recipient Support

Send to multiple recipients:

```python
await email_service.send(
    to=["user1@example.com", "user2@example.com"],
    cc=["manager@example.com"],
    bcc=["archive@example.com"],
    subject="Team Announcement",
    template="announcement.html",
    context={"message": "Important update"},
)
```

## Attachments

Send files with emails:

```python
await email_service.send(
    to="user@example.com",
    subject="Invoice",
    template="invoice.html",
    attachments=[
        {
            "filename": "invoice.pdf",
            "content": pdf_bytes,
            "mimetype": "application/pdf",
        },
        {
            "filename": "logo.png",
            "content": logo_bytes,
            "mimetype": "image/png",
            "inline": True,
            "cid": "logo",  # Reference in template: <img src="cid:logo">
        },
    ],
)
```

## Async Delivery

Background email sending with FastAPI:

```python
from fastapi import BackgroundTasks


@app.post("/register")
async def register(email: str, background_tasks: BackgroundTasks):
    # Register user logic...

    # Send welcome email in background
    background_tasks.add_task(
        email_service.send,
        to=email,
        subject="Welcome!",
        template="welcome.html",
        context={"username": "Alice"},
    )

    return {"status": "registered"}
```

## Testing

Mock email backend for testing:

```python
from src.modules.free.communication.email.testing import MockEmailBackend

# In tests
email_service = EmailService(transport=MockEmailBackend())

await email_service.send(to="test@example.com", subject="Test", template="test.html")

# Check sent emails
assert len(email_service.transport.sent_emails) == 1
assert email_service.transport.sent_emails[0]["to"] == "test@example.com"
```

## Health Monitoring

Health endpoint reports:

- Transport connectivity status
- Recent delivery success/failure rates
- Template availability
- Queue depth (if using async queue)

```json
{
  "status": "healthy",
  "module": "email",
  "transport": {
    "type": "smtp",
    "connected": true,
    "host": "smtp.gmail.com"
  },
  "templates": {
    "available": 15,
    "missing": []
  },
  "metrics": {
    "sent_last_hour": 142,
    "failed_last_hour": 0
  }
}
```

Access health status at `/api/health/module/email`.

## Error Handling

Graceful failure handling:

```python
from src.modules.free.communication.email.exceptions import (
    EmailDeliveryError,
    TemplateNotFoundError,
    TransportConnectionError,
)

try:
    await email_service.send(to="user@example.com", template="welcome.html")
except TemplateNotFoundError as e:
    logger.error(f"Template not found: {e.template_name}")
except TransportConnectionError as e:
    logger.error(f"Transport connection failed: {e}")
except EmailDeliveryError as e:
    logger.error(f"Email delivery failed: {e}")
```

## Supported Frameworks

- **FastAPI**: Full async support with dependency injection
- **NestJS**: Injectable service with TypeScript definitions
- **Flask**: Sync support with Flask-Mail compatibility
- **Custom**: Direct service instantiation for other frameworks

## Security Features

- **TLS/SSL**: Encrypted transport connections
- **API key management**: Secure credential storage
- **Template sanitization**: XSS protection in HTML templates
- **SPF/DKIM**: Recommended DNS records for deliverability
- **Rate limiting**: Transport-level rate limit handling

## Performance Features

- **Connection pooling**: Reuse SMTP connections
- **Async delivery**: Non-blocking email sending
- **Batch sending**: Efficient multi-recipient delivery
- **Template caching**: Pre-compiled Jinja2 templates

## Getting Help

- **Usage Guide**: Setup instructions and common patterns
- **Advanced Guide**: Custom transports and template helpers
- **Troubleshooting**: Delivery issues and debugging
- **Migration Guide**: Upgrading from previous versions

For issues and questions, visit our
[GitHub repository](https://github.com/getrapidkit/rapidkit-core).
