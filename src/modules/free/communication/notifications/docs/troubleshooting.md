# Notifications Module - Troubleshooting Guide

Solutions for common issues and debugging strategies when using the notifications module.

## Connection Issues

### SMTP Connection Failed

**Error:**

```
SMTP connection error: [Errno -2] Name or service not known
```

**Causes & Solutions:**

1. **Incorrect hostname**

   ```python
   # ✗ Wrong
   config = EmailConfig(host="sendgrid.net", ...)

   # ✓ Correct
   config = EmailConfig(host="smtp.sendgrid.net", ...)
   ```

1. **Firewall/Network blocked**

   - Verify port is open: `telnet smtp.sendgrid.net 587`
   - Check firewall rules allow outbound SMTP
   - Verify network connectivity: `ping smtp.sendgrid.net`

1. **Wrong credentials**

   ```bash
   # Test with telnet
   telnet smtp.sendgrid.net 587
   ehlo test
   auth login
   # Enter username/password
   ```

1. **Environment variables not loaded**

   ```python
   import os

   # Debug: Print loaded values (not passwords!)
   print(f"SMTP Host: {os.getenv('RAPIDKIT_NOTIFICATIONS_SMTP_HOST')}")
   print(f"SMTP Port: {os.getenv('RAPIDKIT_NOTIFICATIONS_SMTP_PORT')}")

   # Ensure variables are set
   if not os.getenv("RAPIDKIT_NOTIFICATIONS_SMTP_HOST"):
       raise RuntimeError("RAPIDKIT_NOTIFICATIONS_SMTP_HOST not set")
   ```

### Timeout on SMTP Connection

**Error:**

```
ConnectionError: connect() takes at most 3 positional arguments
```

**Solution:**

Increase timeout:

```python
config = EmailConfig(
    host="smtp.sendgrid.net",
    port=587,
    username="apikey",
    password=os.getenv("SENDGRID_API_KEY"),
    from_email="noreply@example.com",
    timeout=60,  # Increase from default 30 seconds
)
```

Or verify SMTP connection explicitly:

```python
import asyncio


async def test_connection():
    service = EmailService(config)
    is_connected = await service.verifyConnection()
    print(f"Connected: {is_connected}")


asyncio.run(test_connection())
```

### TLS/SSL Certificate Error

**Error:**

```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solution:**

1. **Verify TLS is enabled correctly**

   ```python
   config = EmailConfig(
       host="smtp.example.com", port=465, use_tls=True, ...  # Use 465 for SSL
   )
   ```

1. **For self-signed certificates in development**

   ```python
   import ssl

   # Only for development! Never use in production
   ssl_context = ssl.create_default_context()
   ssl_context.check_hostname = False
   ssl_context.verify_mode = ssl.CERT_NONE

   # Then pass to transporter (requires aiosmtplib configuration)
   ```

## Authentication Issues

### Invalid SMTP Credentials

**Error:**

```
SMTPAuthenticationError: (535, b'5.7.8 Username and password not accepted')
```

**Solutions:**

1. **Verify credentials in test script**

   ```python
   import smtplib

   try:
       smtp = smtplib.SMTP("smtp.sendgrid.net", 587)
       smtp.starttls()
       smtp.login("apikey", "SG.your-api-key")
       smtp.quit()
       print("Credentials valid")
   except smtplib.SMTPAuthenticationError as e:
       print(f"Authentication failed: {e}")
   ```

1. **Check for spaces or special characters**

   ```bash
   # ✗ Wrong - extra space
   export RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD="SG.key "

   # ✓ Correct
   export RAPIDKIT_NOTIFICATIONS_SMTP_PASSWORD="SG.key"
   ```

1. **Verify provider requirements**

   - SendGrid: Use "apikey" as username with API key as password
   - Mailgun: Use full email as username
   - AWS SES: Use IAM credentials, not account password

### Permission Denied

**Error:**

```
SMTPSenderRefused: (550, b'User does not have permission')
```

**Solution:**

Use verified "From" address:

```python
# ✗ Wrong - unverified address
config = EmailConfig(from_email="random@unverified.com", ...)

# ✓ Correct - verified with provider
config = EmailConfig(from_email="verified@yourdomain.com", ...)
```

## Email Delivery Issues

### Emails Not Received

**Checklist:**

1. **Verify email was actually sent**

   ```python
   message = EmailMessage(
       to=["recipient@example.com"], subject="Test", html="<p>Test email</p>"
   )

   success = await email_service.send_email(message)
   print(f"Send result: {success}")  # Should be True
   ```

1. **Check spam folder**

   - Emails may be filtered by recipient's email provider
   - Add proper headers:
     ```python
     message = EmailMessage(
         to=["user@example.com"],
         subject="Test",
         html="<p>Test</p>",
         headers={
             "X-Priority": "3",
             "List-Unsubscribe": "<https://example.com/unsubscribe>",
         },
     )
     ```

1. **Verify recipient address**

   ```python
   from email_validator import validate_email

   try:
       validate_email("recipient@example.com")
   except Exception as e:
       print(f"Invalid email: {e}")
   ```

1. **Check email headers**

   - Add diagnostic headers:
     ```python
     message = EmailMessage(
         to=["user@example.com"],
         subject="Test",
         html="...",
         headers={"X-Mailer": "RapidKit/0.1.0", "X-Priority": "3"},
     )
     ```

### HTML Not Rendering Correctly

**Issue:** Email client shows raw HTML or formatting is broken

**Solutions:**

1. **Use proper MIME types** (automatic in module)

   ```python
   # The module handles this automatically
   message = EmailMessage(html="<h1>Title</h1><p>Content</p>")
   # Sent with text/html MIME type
   ```

1. **Inline CSS for email compatibility**

   ```html
   <!-- ✗ External CSS won't work in emails -->
   <link rel="stylesheet" href="style.css">

   <!-- ✓ Inline styles work -->
   <p style="color: blue; font-size: 16px;">Text</p>
   ```

1. **Use email-safe fonts**

   ```html
   <p style="font-family: 'Arial', 'Helvetica', sans-serif;">
     Use web-safe fonts only
   </p>
   ```

1. **Test in Email on Acid**

   - Use online tools to test HTML email rendering
   - Litmus, Email on Acid, or similar services

### Large Attachments Failing

**Error:**

```
MessageSizeLimitExceeded: Message size exceeds limit
```

**Solution:**

Email providers have size limits (typically 25MB). For large files:

```python
# Instead of attaching to email, use file storage
async def send_with_download_link(email_service, recipient, file_path):
    # Upload file to S3/cloud storage
    file_url = await upload_to_s3(file_path)

    message = EmailMessage(
        to=[recipient],
        subject="Your File",
        html=f'<p><a href="{file_url}">Download file</a></p>',
    )

    return await email_service.send_email(message)
```

## Template Issues

### Template Not Found

**Error:**

```
FileNotFoundError: Template not found: welcome
```

**Solution:**

1. **Set template directory first**

   ```python
   email_service.setTemplateDirectory("templates/emails")

   # Verify directory exists
   import os

   print(os.path.exists("templates/emails"))  # Should be True
   ```

1. **Check template file name**

   ```bash
   # ✗ Wrong - missing .hbs extension
   ls templates/emails/welcome

   # ✓ Correct
   ls templates/emails/welcome.hbs
   ```

1. **Verify file permissions**

   ```bash
   ls -la templates/emails/welcome.hbs
   # Should be readable (r permission)
   ```

### Template Rendering Fails

**Error:**

```
jinja2.exceptions.UndefinedError: 'name' is undefined
```

**Solution:**

Verify context variables match template:

```handlebars
<!-- welcome.hbs -->
<h1>Hello {{name}}</h1>
```

Python example:

```python
# ✓ Correct - 'name' provided
await email_service.sendTemplatedEmail(
    to=[recipient], template_name="welcome", context={"name": "John"}, subject="Welcome"
)

# ✗ Wrong - 'name' missing
await email_service.sendTemplatedEmail(
    to=[recipient],
    template_name="welcome",
    context={},  # Missing 'name'!
    subject="Welcome",
)
```

### Template Caching Issues

**Problem:** Changes to template files not reflected

**Solution:**

Clear cache:

```python
# Disable caching during development
os.environ["RAPIDKIT_NOTIFICATIONS_ENABLE_TEMPLATE_CACHING"] = "false"

# Or clear manually
email_service.templateCache.clear()

# For production, restart application to reload templates
```

## Rate Limiting

### Too Many Emails Sent

**Error:**

```
SMTPDataError: (452, b'Too many emails sent')
```

**Solutions:**

1. **Implement rate limiting**

   ```python
   from time import time


   class RateLimitedEmailService:
       def __init__(self, emails_per_minute: int = 100):
           self.emails_per_minute = emails_per_minute
           self.sent_times = []

       async def send_email(self, message):
           now = time()
           # Remove old entries
           self.sent_times = [t for t in self.sent_times if now - t < 60]

           if len(self.sent_times) >= self.emails_per_minute:
               wait_time = 60 - (now - self.sent_times[0])
               raise Exception(f"Rate limit exceeded, retry in {wait_time}s")

           self.sent_times.append(now)
           return await super().send_email(message)
   ```

1. **Use queue with delays**

   ```python
   import asyncio
   from collections import deque

   email_queue = deque()


   async def process_queue_with_delay(email_service, delay_ms=100):
       while email_queue:
           message = email_queue.popleft()
           await email_service.send_email(message)
           await asyncio.sleep(delay_ms / 1000)
   ```

1. **Check provider rate limits**

   - SendGrid: 300 requests/second
   - Mailgun: Depends on account level
   - AWS SES: 14 emails/second (sandbox) or up to 50/second (prod)

## Performance Issues

### Slow Email Sending

**Problem:** Email takes >5 seconds to send

**Debugging:**

```python
import time


async def send_with_timing(email_service, message):
    start = time.time()

    try:
        result = await email_service.send_email(message)
        elapsed = time.time() - start
        print(f"Email sent in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"Email failed after {elapsed:.2f}s: {e}")
        raise
```

**Solutions:**

1. **Increase timeout**

   ```python
   config = EmailConfig(..., timeout=60)
   ```

1. **Use async/background tasks**

   ```python
   from fastapi import BackgroundTasks


   @app.post("/send")
   async def send_email_bg(background_tasks: BackgroundTasks):
       background_tasks.add_task(email_service.send_email, message)
       return {"status": "queued"}
   ```

1. **Use connection pooling**

   - Keep SMTP connection open instead of reconnecting

## Debugging Strategies

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Enable aiosmtplib debugging
logging.getLogger("aiosmtplib").setLevel(logging.DEBUG)

# Enable email validation debugging
logging.getLogger("email_validator").setLevel(logging.DEBUG)
```

### Health Check Diagnostics

```python
async def diagnose():
    """Run comprehensive diagnostics."""
    print("=== Email Service Diagnostics ===")

    config = EmailConfig(...)
    service = EmailService(config)

    # Test connection
    try:
        connected = await service.verifyConnection()
        print(f"✓ SMTP Connection: {'OK' if connected else 'FAILED'}")
    except Exception as e:
        print(f"✗ SMTP Connection: {str(e)}")

    # Test template directory
    try:
        service.setTemplateDirectory("templates/emails")
        print("✓ Template Directory: OK")
    except Exception as e:
        print(f"✗ Template Directory: {str(e)}")

    # Test template rendering
    try:
        html = service.renderTemplate("test", {"name": "Test"})
        print("✓ Template Rendering: OK")
    except Exception as e:
        print(f"✗ Template Rendering: {str(e)}")

    print("\nStatus:", service.getStatus())


asyncio.run(diagnose())
```

### Common Logs to Check

```bash
# Check application logs
tail -f logs/app.log | grep -i "notification\|email"

# Check system mail logs
tail -f /var/log/mail.log

# Check SMTP connection logs
tail -f /var/log/syslog | grep SMTP
```

## Getting Help

1. **Check module health endpoint**

   ```bash
   curl http://localhost:8000/health/notifications -i
   ```

1. **Enable debug mode**

   - Set `DEBUG=true` environment variable
   - Check logs for detailed error messages

1. **Test with minimal example**

   ```python
   # Minimal reproducible example
   config = EmailConfig(host="...", port=587, ...)
   service = EmailService(config)
   success = await service.send_email(EmailMessage(...))
   ```

1. **Consult provider docs**

   - SendGrid: https://docs.sendgrid.com
   - Mailgun: https://documentation.mailgun.com
   - AWS SES: https://docs.aws.amazon.com/ses

1. **File issue on GitHub**

   - Include error message, stack trace, and minimal reproducible example
   - Don't include API keys or credentials!
