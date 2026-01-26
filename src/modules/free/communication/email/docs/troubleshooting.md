# Troubleshooting

Common issues and resolutions for the RapidKit Email module.

## SMTP Connection Fails

- **Symptom:** `EmailDeliveryError` with `provider='smtp'` or `SMTPServerDisconnected`.
- **Fix:**
  - Verify `RAPIDKIT_EMAIL_SMTP_HOST`/`PORT` and credentials.
  - Enable TLS only if the server supports it.
  - Run `await service.verify_connection()` or the generated health endpoint to confirm access.

## Optional Dependencies Missing

- **Symptom:** Runtime errors indicating `jinja2` or `aiosmtplib` is not installed.
- **Fix:** Install the extras listed in the usage guide or pin them in your project requirements.

## Templates Not Rendering

- **Symptom:** Empty HTML body or warnings about missing templates.
- **Fix:**
  - Ensure `RAPIDKIT_EMAIL_TEMPLATE_DIRECTORY` points to a real path deployed with your service.
  - Enable `template.strict: true` to fail fast in non-production environments.
  - For NestJS, confirm the template file names match the ones passed to `sendTemplatedEmail`.

## Messages Not Delivered but Console Logs Appear

- **Symptom:** Payload logged but no outbound email.
- **Fix:**
  - Check whether `RAPIDKIT_EMAIL_PROVIDER=console` or `dryRun` is enabled.
  - Disable console mode in staging/production environments.

## Duplicate Headers or Invalid Addresses

- **Symptom:** SMTP rejects messages due to malformed headers.
- **Fix:**
  - Validate payload data with `EmailMessagePayload` to normalise addresses.
  - Use `default_headers` sparingly and ensure values meet RFC standards.
  - Sanitize user-supplied strings before injecting them into headers or subjects.

## High Latency Under Load

- **Symptom:** Notification endpoints slow when sending bursts of email.
- **Fix:**
  - Offload to background workers or asynchronous queues.
  - Provide a custom transport with connection pooling to keep sessions warm.
  - Monitor via tracing and metrics to detect provider throttling.
