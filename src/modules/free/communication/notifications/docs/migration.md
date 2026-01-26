# Notifications Module - Migration Guide

Guide for upgrading between versions and migrating from other notification systems.

## Version Migration

### 0.1.x → 0.2.0 (Future)

When 0.2.0 is released, it will include:

- Support for SMS notifications (Twilio integration)
- Support for push notifications (Firebase Cloud Messaging)
- Enhanced template syntax (more Handlebars helpers)
- Performance improvements

**Upgrade steps (when available):**

```bash
# Update module
rapidkit modules upgrade notifications

# Run migration scripts if needed
poetry run python scripts/migrate-notifications-0.1-to-0.2.py

# Test
poetry run pytest tests/modules/free_communication_notifications -v
```

## Migrating from Other Email Services

### From Flask-Mail

**Before:**

```python
from flask_mail import Mail, Message

mail = Mail(app)

msg = Message(subject="Hello", recipients=["user@example.com"], html="<h1>Hello</h1>")
mail.send(msg)
```

**After:**

```python
from src.modules.free.communication.notifications.core.notifications import (
    EmailService,
    EmailMessage,
)

service = EmailService(config)

message = EmailMessage(to=["user@example.com"], subject="Hello", html="<h1>Hello</h1>")
await service.send_email(message)
```

### From Django Email Backend

**Before:**

```python
from django.core.mail import send_mail

send_mail(
    "Subject",
    "Message body",
    "from@example.com",
    ["to@example.com"],
    html_message="<h1>HTML</h1>",
)
```

**After:**

```python
from src.modules.free.communication.notifications.core.notifications import (
    EmailService,
    EmailMessage,
)

service = EmailService(config)

message = EmailMessage(to=["to@example.com"], subject="Subject", html="<h1>HTML</h1>")
await service.send_email(message)
```

### From Celery + Mailchimp

**Before:**

```python
from celery import shared_task
from mailchimp_marketing import Client


@shared_task
def send_campaign_email(email, campaign_id):
    client = Client()
    client.set_config({"api_key": settings.MAILCHIMP_API_KEY, "server": "us1"})
    # Complex campaign logic...
```

**After:**

```python
from src.modules.free.communication.notifications.core.notifications import (
    NotificationManager,
)


async def send_campaign_email(email, campaign_id):
    notification = Notification(
        type=NotificationType.EMAIL,
        recipient=email,
        title="Campaign Title",
        body="Campaign content",
        template=f"campaign-{campaign_id}",
        context={"campaign_id": campaign_id},
    )

    manager = NotificationManager()
    await manager.send_notification(notification)
```

### From SendGrid Python Library

**Before:**

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

message = Mail(
    from_email="from@example.com",
    to_emails="to@example.com",
    subject="Sending with Twilio SendGrid is Fun",
    html_content="<strong>and easy to do anywhere, even with Python</strong>",
)

response = sg.send(message)
```

**After:**

```python
from src.modules.free.communication.notifications.core.notifications import (
    EmailService,
    EmailConfig,
)

config = EmailConfig(
    host="smtp.sendgrid.net",
    port=587,
    username="apikey",
    password=os.getenv("SENDGRID_API_KEY"),
    from_email="from@example.com",
)

service = EmailService(config)

message = EmailMessage(
    to=["to@example.com"],
    subject="Sending with Twilio SendGrid is Fun",
    html="<strong>and easy to do anywhere, even with Python</strong>",
)

await service.send_email(message)
```

## Batch Notification Migration

### From MongoDB to PostgreSQL Queues

**Before (MongoDB):**

```python
from pymongo import MongoClient

client = MongoClient()
db = client["notifications"]
collection = db["pending_emails"]


async def send_batch():
    pending = collection.find({"status": "pending"}).limit(100)
    for doc in pending:
        # send email
        collection.update_one({"_id": doc["_id"]}, {"$set": {"status": "sent"}})
```

**After (PostgreSQL):**

```python
from src.modules.free.communication.notifications.core.notifications import EmailQueue


class NotificationQueue(EmailQueue):
    async def process_pending(self):
        pending = await self.db.fetch(
            """
            SELECT * FROM email_queue
            WHERE status = 'pending'
            LIMIT 100
        """
        )

        for row in pending:
            # send email
            await self.db.execute(
                "UPDATE email_queue SET status = 'sent' WHERE id = %s", [row["id"]]
            )


# Usage
queue = NotificationQueue(db_connection)
await queue.process_pending()
```

## Template Migration

### From Jinja2 Templates

**Before:**

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("email.html")
html = template.render(name="John", order_id="12345")
```

**After:**

```python
from src.modules.free.communication.notifications.core.notifications import EmailService

service = EmailService(config)
service.setTemplateDirectory("templates")

html = service.renderTemplate("email", {"name": "John", "order_id": "12345"})
```

### From EJS Templates (NestJS/Node)

**Before (NestJS):**

```typescript
import * as ejs from 'ejs';

const html = ejs.render(template, {
  name: 'John',
  orderId: '12345'
});
```

**After (NestJS with Notifications Module):**

```typescript
import { EmailService } from './notifications.service';

export class MyService {
  constructor(private emailService: EmailService) {}

  async sendEmail(name: string, orderId: string) {
    this.emailService.setTemplateDirectory('templates/emails');

    const html = this.emailService.renderTemplate('email', {
      name,
      orderId
    });

    return this.emailService.sendEmail({
      to: [email],
      subject: 'Order Confirmation',
      html
    });
  }
}
```

## Provider Migration

### From AWS SES to SendGrid

**Step 1: Update credentials**

```bash
# Remove AWS credentials
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY

# Add SendGrid API key
export RAPIDKIT_NOTIFICATIONS_SMTP_HOST=smtp.sendgrid.net
export RAPIDKIT_NOTIFICATIONS_SMTP_PORT=587
export RAPIDKIT_NOTIFICATIONS_SMTP_USERNAME=apikey
export RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD=SG.your-key
```

**Step 2: Update configuration**

```python
# Before (AWS SES)
import boto3

ses_client = boto3.client("ses", region_name="us-east-1")

# After (SendGrid)
from src.modules.free.communication.notifications.core.notifications import EmailConfig

config = EmailConfig(
    host="smtp.sendgrid.net",
    port=587,
    username="apikey",
    password=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD"),
    from_email="noreply@example.com",
)
```

**Step 3: Update sender address**

```python
# AWS SES - Must verify in SES console
# SendGrid - Can use any domain (but SPF/DKIM recommended)

config.from_email = "noreply@example.com"
```

**Step 4: Monitor during transition**

```bash
# Check health endpoint frequently during migration
curl http://localhost:8000/health/notifications

# Monitor delivery rates
tail -f logs/notifications.log | grep -i delivered
```

### From Mailgun to SendGrid

**Key differences:**

| Feature             | Mailgun            | SendGrid                 |
| ------------------- | ------------------ | ------------------------ |
| Domain verification | Required           | Optional but recommended |
| Webhook format      | Different          | Different                |
| Rate limits         | Flexible           | 300/sec default          |
| Cost model          | Per email + events | Fixed + events           |

**Migration steps:**

```bash
# 1. Export events from Mailgun
mailgun-cli events export --domain=mg.example.com

# 2. Update SMTP configuration
export RAPIDKIT_NOTIFICATIONS_SMTP_HOST=smtp.sendgrid.net
export RAPIDKIT_NOTIFICATIONS_SMTP_USERNAME=apikey
export RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD=SG.key

# 3. Verify domain
# SendGrid console: Settings → Sender Authentication

# 4. Test with small batch
# Send test emails to ensure delivery

# 5. Cutover
# Update all email sending to use new config
```

## Database Schema Migration

### Adding Notification History

If you want to track sent notifications:

```sql
-- Create notification history table
CREATE TABLE email_history (
    id SERIAL PRIMARY KEY,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    error_message TEXT,
    provider VARCHAR(50),
    email_id VARCHAR(255),
    delivery_status VARCHAR(50)
);

-- Create index for queries
CREATE INDEX idx_email_history_recipient ON email_history(recipient);
CREATE INDEX idx_email_history_sent_at ON email_history(sent_at DESC);
```

### Indexing for Performance

```sql
-- Index for queue processing
CREATE INDEX idx_queue_status ON email_queue(status, created_at);

-- Index for retry logic
CREATE INDEX idx_queue_retry ON email_queue(retry_count, created_at);

-- Composite index for common queries
CREATE INDEX idx_queue_composite ON email_queue(status, retry_count, created_at);
```

## API Compatibility

### Backwards Compatible Changes

The module maintains backwards compatibility for:

- `EmailMessage` field additions (old code still works)
- `send_email()` method signature
- Health check endpoint format

### Breaking Changes (Future Versions)

None planned for 0.1.x → 0.2.0, but when they occur:

- New method signatures will be released in major version
- Old methods will be marked `@deprecated`
- Migration guides will be provided

## Testing Migration

### Verify Email Delivery

```python
import asyncio


async def verify_migration():
    """Test email delivery after migration."""

    config = EmailConfig(
        host=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_HOST"),
        port=int(os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_PORT", "587")),
        username=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_USERNAME"),
        password=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD"),
        from_email=os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_FROM"),
    )

    service = EmailService(config)

    # Test 1: Connection
    connected = await service.verifyConnection()
    print(f"Connection: {'✓' if connected else '✗'}")

    # Test 2: Simple email
    message = EmailMessage(
        to=["test@example.com"],
        subject="Migration Test",
        html="<p>Migration test email</p>",
    )
    sent = await service.send_email(message)
    print(f"Send email: {'✓' if sent else '✗'}")

    # Test 3: Template rendering
    service.setTemplateDirectory("templates")
    try:
        html = service.renderTemplate("test", {"name": "Test"})
        print(f"Template rendering: ✓")
    except Exception as e:
        print(f"Template rendering: ✗ ({e})")


asyncio.run(verify_migration())
```

### Parallel Running

Run old and new systems in parallel for safety:

```python
import asyncio
from old_service import OldEmailService
from src.modules.free.communication.notifications.core.notifications import (
    EmailService as NewEmailService,
)


async def send_with_fallback(message, old_service, new_service):
    """Try new service first, fall back to old if needed."""

    try:
        success = await new_service.send_email(message)
        if success:
            return True
    except Exception as e:
        logger.error(f"New service failed: {e}")

    # Fallback to old service
    logger.info("Falling back to old email service")
    try:
        return await old_service.send_email(message)
    except Exception as e:
        logger.error(f"Old service also failed: {e}")
        return False
```

## Rollback Plan

If migration fails:

```bash
# 1. Restore previous configuration
export RAPIDKIT_NOTIFICATIONS_SMTP_HOST=$PREVIOUS_SMTP_HOST
export RAPIDKIT_NOTIFICATIONS_SMTP_USERNAME=$PREVIOUS_USERNAME
export RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD=$PREVIOUS_PASSWORD

# 2. Restart application
systemctl restart myapp

# 3. Verify health
curl http://localhost:8000/health/notifications

# 4. Check logs
tail -f logs/notifications.log
```

## Support and Questions

- **Documentation:** See usage.md, advanced.md, troubleshooting.md
- **Issues:** File on GitHub with migration details
- **Email Vendor Support:**
  - SendGrid: https://support.sendgrid.com
  - Mailgun: https://documentation.mailgun.com
  - AWS SES: https://docs.aws.amazon.com/ses
