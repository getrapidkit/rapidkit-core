# Notifications Module - Advanced Guide

Advanced patterns, customization, and best practices for production email systems.

## Custom Email Providers

### Using Alternative SMTP Services

The module supports any SMTP-compatible service. Examples:

**SendGrid:**

```python
config = EmailConfig(
    host="smtp.sendgrid.net",
    port=587,
    username="apikey",
    password=os.getenv("SENDGRID_API_KEY"),
    from_email="noreply@example.com",
)
```

**Mailgun:**

```python
config = EmailConfig(
    host="smtp.mailgun.org",
    port=587,
    username="postmaster@sandboxXXX.mailgun.org",
    password=os.getenv("MAILGUN_SMTP_PASSWORD"),
    from_email="noreply@example.com",
)
```

**AWS SES:**

```python
config = EmailConfig(
    host="email-smtp.us-east-1.amazonaws.com",
    port=587,
    username=os.getenv("AWS_SES_USERNAME"),
    password=os.getenv("AWS_SES_PASSWORD"),
    from_email="noreply@example.com",
)
```

**Local Development (Mailtrap):**

```python
config = EmailConfig(
    host="smtp.mailtrap.io",
    port=587,
    username=os.getenv("MAILTRAP_USERNAME"),
    password=os.getenv("MAILTRAP_PASSWORD"),
    from_email="noreply@localhost",
)
```

## Template Rendering

### Advanced Template Features

**Handlebars Helpers:**

```handlebars
{{#if premium}}
  <p>Premium feature: {{feature}}</p>
{{else}}
  <p>Upgrade to premium to access this feature</p>
{{/if}}

{{#each items}}
  <li>{{this.name}} - ${{this.price}}</li>
{{/each}}
```

### Nested Template Context

```python
context = {
    "user": {
        "name": "John Doe",
        "email": "john@example.com",
        "preferences": {"notifications_enabled": True},
    },
    "order": {
        "id": "ORD-12345",
        "items": [{"name": "Widget", "quantity": 2}, {"name": "Gadget", "quantity": 1}],
        "total": 99.99,
    },
    "company": "Acme Corp",
}

html = email_service.render_template("order-confirmation", context)
```

**Template file (order-confirmation.hbs):**

```handlebars
<h1>Order Confirmation</h1>
<p>Hi {{user.name}},</p>
<p>Your order from {{company}} has been confirmed!</p>

<h2>Order Details</h2>
<ul>
  {{#each order.items}}
    <li>{{this.name}} x {{this.quantity}}</li>
  {{/each}}
</ul>
<p><strong>Total:</strong> ${{order.total}}</p>

{{#if user.preferences.notifications_enabled}}
  <p>You'll receive updates about your order at {{user.email}}</p>
{{/if}}
```

### Template Caching Control

Cache is enabled by default for performance:

```python
# Disable caching for development
email_service.templateCache.clear()

# Or set environment variable
os.environ["RAPIDKIT_NOTIFICATIONS_ENABLE_TEMPLATE_CACHING"] = "false"
```

## Batch Email Sending

### Send to Multiple Recipients

```python
recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

message = EmailMessage(
    to=recipients,
    subject="Batch Announcement",
    html="<p>Important update for all users</p>",
)

success = await email_service.send_email(message)
```

### Personalized Batch Sending

```python
async def send_personalized_batch(users: List[dict], template: str):
    results = []

    for user in users:
        try:
            success = await email_service.send_templated_email(
                to=[user["email"]],
                template_name=template,
                context={
                    "name": user["name"],
                    "id": user["id"],
                    "preferences": user.get("preferences", {}),
                },
                subject=f"Hello {user['name']}!",
            )
            results.append(
                {"email": user["email"], "status": "sent" if success else "failed"}
            )
        except Exception as e:
            results.append({"email": user["email"], "status": "error", "error": str(e)})

    return results
```

## Retry Logic

### Exponential Backoff

```python
import asyncio
import random
from typing import Optional


async def send_with_retry(
    email_service, message: EmailMessage, max_retries: int = 3, base_delay: float = 1.0
) -> bool:
    """Send email with exponential backoff retry logic."""

    for attempt in range(max_retries):
        try:
            success = await email_service.send_email(message)
            if success:
                return True

            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                delay = base_delay * (2**attempt)
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, delay * 0.1)
                await asyncio.sleep(delay + jitter)

        except Exception as e:
            logger.error(f"Send attempt {attempt + 1} failed: {str(e)}")

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                await asyncio.sleep(delay)

    logger.error(f"Failed to send email after {max_retries} attempts")
    return False
```

### Dead Letter Queue Pattern

```python
from datetime import datetime, timedelta
import json


class EmailQueue:
    def __init__(self, db_connection):
        self.db = db_connection

    async def add_to_queue(self, message: EmailMessage, priority: int = 0):
        """Add email to queue for later delivery."""
        await self.db.execute(
            """
            INSERT INTO email_queue (message, priority, created_at)
            VALUES (%s, %s, %s)
        """,
            [json.dumps(message.dict()), priority, datetime.utcnow()],
        )

    async def process_queue(self, email_service):
        """Process queued emails with retry logic."""
        rows = await self.db.fetch(
            """
            SELECT id, message, retry_count
            FROM email_queue
            WHERE retry_count < 5
            ORDER BY priority DESC, created_at ASC
            LIMIT 100
        """
        )

        for row in rows:
            message_data = json.loads(row["message"])
            message = EmailMessage(**message_data)

            success = await send_with_retry(email_service, message, max_retries=3)

            if success:
                await self.db.execute(
                    "DELETE FROM email_queue WHERE id = %s", [row["id"]]
                )
            else:
                await self.db.execute(
                    "UPDATE email_queue SET retry_count = retry_count + 1 WHERE id = %s",
                    [row["id"]],
                )
```

## Notification Event Hooks

### Custom Notification Handlers

```python
from typing import Callable, Dict


class ExtendedNotificationManager(NotificationManager):
    def __init__(self):
        super().__init__()
        self.pre_send_hooks: List[Callable] = []
        self.post_send_hooks: List[Callable] = []

    def register_pre_send_hook(self, handler: Callable):
        """Run before notification is sent."""
        self.pre_send_hooks.append(handler)

    def register_post_send_hook(self, handler: Callable):
        """Run after notification is sent."""
        self.post_send_hooks.append(handler)

    async def send_notification(self, notification) -> bool:
        # Run pre-send hooks
        for hook in self.pre_send_hooks:
            await hook(notification)

        # Send notification
        result = await super().send_notification(notification)

        # Run post-send hooks
        for hook in self.post_send_hooks:
            await hook(notification, result)

        return result


# Usage:
manager = ExtendedNotificationManager()


async def log_sent_email(notification, success):
    logger.info(f"Email to {notification.recipient}: {'sent' if success else 'failed'}")


manager.register_post_send_hook(log_sent_email)
```

### Analytics and Metrics

```python
from prometheus_client import Counter, Histogram
import time

# Prometheus metrics
email_sent_counter = Counter("email_sent_total", "Total emails sent", ["status"])

email_send_duration = Histogram("email_send_duration_seconds", "Email send duration")


async def send_with_metrics(email_service, message):
    start = time.time()
    try:
        success = await email_service.send_email(message)
        email_sent_counter.labels(status="success" if success else "failed").inc()
        return success
    except Exception as e:
        email_sent_counter.labels(status="error").inc()
        raise
    finally:
        duration = time.time() - start
        email_send_duration.observe(duration)
```

## Security Best Practices

### SMTP Authentication

```python
# ✓ GOOD: Use environment variables
config = EmailConfig(
    host=os.getenv("SMTP_HOST"),
    username=os.getenv("SMTP_USERNAME"),
    password=os.getenv("SMTP_PASSWORD"),  # Never hardcode!
    from_email=os.getenv("SMTP_FROM"),
)

# ✓ GOOD: Use secrets management
from kubernetes import client

secret = client.CoreV1Api().read_namespaced_secret("smtp-credentials", "default")
config = EmailConfig(
    host=secret.data["host"],
    username=secret.data["username"],
    password=secret.data["password"],
    from_email=secret.data["from"],
)

# ✗ BAD: Hardcoded credentials
config = EmailConfig(
    host="smtp.example.com",
    username="user@example.com",
    password="password123",  # NEVER DO THIS!
    from_email="noreply@example.com",
)
```

### Email Content Validation

```python
import re
from email_validator import validate_email, EmailNotValidError


def validate_recipients(recipients: List[str]) -> bool:
    """Validate email addresses before sending."""
    for email in recipients:
        try:
            validate_email(email)
        except EmailNotValidError as e:
            logger.error(f"Invalid email address: {email} - {str(e)}")
            return False
    return True


async def send_safe(email_service, message: EmailMessage):
    """Send email with validation."""
    if not validate_recipients(message.to):
        raise ValueError("One or more invalid recipient emails")

    if message.cc and not validate_recipients(message.cc):
        raise ValueError("One or more invalid CC emails")

    return await email_service.send_email(message)
```

### Content Sanitization

```python
from bleach import clean


def sanitize_email_content(html: str) -> str:
    """Remove potentially dangerous HTML/scripts from email content."""
    allowed_tags = ["p", "a", "ul", "ol", "li", "strong", "em", "h1", "h2", "h3", "img"]
    allowed_attributes = {"a": ["href"], "img": ["src", "alt"]}

    return clean(html, tags=allowed_tags, attributes=allowed_attributes)


# Usage:
html = sanitize_email_content(user_provided_html)
message = EmailMessage(to=[recipient], subject="...", html=html)
```

## Monitoring and Debugging

### Detailed Logging

```python
import logging

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("notifications")


# Add custom logger with contextual information
class ContextualEmailService(EmailService):
    async def send_email(self, message: EmailMessage) -> bool:
        logger.debug(f"Sending email to {message.to}, subject: {message.subject}")

        try:
            result = await super().send_email(message)
            logger.info(f"Email sent successfully to {message.to}")
            return result
        except Exception as e:
            logger.exception(f"Failed to send email to {message.to}: {str(e)}")
            raise
```

### Health Check Monitoring

```python
async def health_check_with_details():
    """Enhanced health check with diagnostic information."""
    email_service = EmailService(config)

    try:
        connected = await email_service.verifyConnection()
        status_details = email_service.getStatus()

        return {
            "status": "healthy" if connected else "unhealthy",
            "smtp_connected": connected,
            "templates_cached": status_details["templatesAvailable"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
```

## Performance Optimization

### Connection Pooling

```python
from aiosmtplib import SMTP


class PooledEmailService(EmailService):
    def __init__(self, config, pool_size: int = 5):
        super().__init__(config)
        self.pool_size = pool_size
        self.pool = asyncio.Queue(maxsize=pool_size)

    async def initialize_pool(self):
        """Pre-create SMTP connections."""
        for _ in range(self.pool_size):
            smtp = SMTP(...)
            await smtp.connect()
            await self.pool.put(smtp)

    async def get_connection(self):
        return await self.pool.get()

    async def return_connection(self, smtp):
        await self.pool.put(smtp)
```

## Next Steps

- See **troubleshooting.md** for common issues and debugging strategies
- See **migration.md** for upgrading to newer versions
- See **usage.md** for quick start examples
