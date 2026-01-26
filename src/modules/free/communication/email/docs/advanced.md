# Advanced

This section outlines advanced configuration patterns and extension points for the Email module.

## Custom Transports

- Implement a coroutine matching `TransportCallable` signature to route messages to third-party APIs
  such as SendGrid or AWS SES.
- Pass it to `EmailService(config, transport=my_callable)` and reuse the built-in message
  construction logic.
- Return a provider-specific message ID string to enrich observability metadata.

## SMTP Hardening

- Enable TLS (`use_tls: true`) and raise `timeout_seconds` if working with slow servers.
- Provide per-environment credentials via RapidKit secrets or platform key vaults.
- Pair `verify_connection()` with your deployment health checks to fail fast on invalid credentials.

## Advanced Templating

- Enable strict mode to raise on missing templates by setting `template.strict: true`.
- Register Jinja filters by customizing the renderer before rendering:
  ```python
  renderer = EmailTemplateRenderer(config.template)
  renderer.configure(Path("templates/email"))
  renderer._environment.filters["currency"] = format_currency
  ```
- In NestJS, precompile Handlebars partials and helpers on module bootstrap to share across
  templates.

## Overriding Defaults

- Add enterprise-specific headers or metadata via the override contract (for example
  `EmailOverrides`).
- Store common header values in `default_headers` to avoid duplication across payloads.
- Set `dryRun: true` in configuration to exercise rendering pipelines without contacting external
  transports.

## Concurrency & Rate Control

- The Python runtime serialises SMTP calls with an async lock to protect connection reuse; override
  by injecting a custom transport that implements your pooling strategy.
- Combine with the RapidKit scheduler or rate-limiting module to throttle high-volume blasts.

## Observability

- Wrap `send_email` calls with your tracing middleware to capture provider latency.
- Inspect the `EmailSendResult` metadata to enrich logs, metrics, or downstream audit trails.
- Register the provided FastAPI and NestJS health helpers inside your platform’s observability
  dashboard.
