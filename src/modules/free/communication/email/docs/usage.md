# Usage

This guide explains how to enable the RapidKit Email module, connect it to transports, and send
templated messages from Python, FastAPI, and NestJS projects.

## Prerequisites

- Python `>=3.10` for the vendor runtime and FastAPI variant.
- Node.js `>=18` for the NestJS variant.
- Optional dependencies:
  - `pip install aiosmtplib` for SMTP delivery.
  - `pip install jinja2` for template rendering.
  - `npm install nodemailer handlebars` for the NestJS service.

## Configure the Module

1. Merge the generated `.env` snippet and adjust values:
   ```bash
   RAPIDKIT_EMAIL_ENABLED=true
   RAPIDKIT_EMAIL_PROVIDER=smtp
   RAPIDKIT_EMAIL_FROM_ADDRESS=noreply@example.com
   RAPIDKIT_EMAIL_FROM_NAME="Example App"
   RAPIDKIT_EMAIL_SMTP_HOST=smtp.example.com
   RAPIDKIT_EMAIL_SMTP_PORT=587
   RAPIDKIT_EMAIL_SMTP_USERNAME=apikey
   RAPIDKIT_EMAIL_SMTP_PASSWORD=super-secret
   RAPIDKIT_EMAIL_SMTP_USE_TLS=true
   RAPIDKIT_EMAIL_TEMPLATE_DIRECTORY=templates/email
   ```
1. Override defaults in `config/base.yaml` when generating a new project:
   ```yaml
   defaults:
     enabled: true
     provider: smtp
     from_email: noreply@example.com
     from_name: Example App
     template:
       directory: services/notifications/templates
       auto_reload: true
       strict: true
   ```

## Python Runtime Usage

```python
from pathlib import Path
from rapidkit.runtime.communication.email import (
    EmailConfig,
    EmailMessagePayload,
    EmailService,
)

config = EmailConfig.from_mapping(
    {
        "provider": "smtp",
        "from_email": "noreply@example.com",
        "smtp": {
            "host": "smtp.example.com",
            "port": 587,
            "username": "apikey",
            "password": "super-secret",
            "use_tls": True,
        },
        "template": {
            "directory": Path("services/notifications/templates"),
            "auto_reload": True,
        },
    }
)

service = EmailService(config)
service.set_template_directory(Path("services/notifications/templates"))

payload = EmailMessagePayload(
    to=["customer@example.com"],
    subject="Welcome!",
    html_body="<p>Hello there.</p>",
    text_body="Hello there.",
)

result = await service.send_email(payload)
print(result.accepted)
```

### Sending Templated Messages

```python
await service.send_templated_email(
    ["customer@example.com"],
    template_name="welcome.html",
    context={"name": "Customer"},
    subject="Welcome aboard",
    text_template="welcome.txt",
)
```

## FastAPI Variant

```python
from fastapi import Depends, FastAPI
from src.modules.free.communication.email.email import EmailService, get_email_service

app = FastAPI()


@app.post("/send")
async def send_email(service: EmailService = Depends(get_email_service)):
    await service.send_templated_email(
        ["customer@example.com"],
        template_name="welcome.html",
        context={"name": "Customer"},
        subject="Welcome!",
    )
    return {"status": "queued"}
```

Include the generated router or call `register_email_health(app)` from `src.health.email` to surface
transport status (`/api/health/module/email`).

## NestJS Variant

```typescript
import { Module } from '@nestjs/common';
import { EmailService, EMAIL_MODULE_CONFIG } from './email/email.service';

@Module({
  providers: [
    EmailService,
    {
      provide: EMAIL_MODULE_CONFIG,
      useValue: {
        enabled: true,
        provider: 'smtp',
        fromAddress: 'noreply@example.com',
        transport: {
          host: 'smtp.example.com',
          port: 587,
          username: 'apikey',
          password: 'super-secret',
          useTls: true,
        },
        template: {
          directory: 'apps/api/templates/email',
          cache: true,
        },
      },
    },
  ],
  exports: [EmailService],
})
export class EmailModule {}
```

Inject `EmailService` wherever you need it and call `sendTemplatedEmail` or `sendEmail`. Use
`createEmailHealthCheck(service)` to feed Terminus health indicators.

## Template Conventions

- Store HTML and text templates in the directory declared in configuration.
- Python uses Jinja2; NestJS uses Handlebars. Keep shared variable names consistent across both.
- Pair HTML and text templates (for example `welcome.html` + `welcome.txt`) to provide graceful
  fallbacks for plaintext clients.
