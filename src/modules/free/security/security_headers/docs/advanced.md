# Advanced Topics

Dig deeper into override patterns, multi-environment deployments, and observability considerations
for the Security Headers module.

## Override Contracts

The generated `SecurityHeadersOverrides` class inherits from `ConfigurableOverrideMixin`. Inside an
enterprise project you can create `core/services/override_contracts.py` and implement:

```python
from core.modules.security import security_headers


class CustomSecurityHeaders(security_headers.SecurityHeadersOverrides):
    def build_headers(self, original, *args, **kwargs):
        headers = original(*args, **kwargs)
        headers["X-Permitted-Cross-Domain-Policies"] = "none"
        return headers
```

Setting `RAPIDKIT_ENABLE_OVERRIDES=1` will cause the runtime wrapper to call through this override,
letting you extend behaviour without forking vendor artefacts.

## Multi-Environment Policies

- **Production** – keep the default Strict-Transport-Security values and provide a full
  Content-Security-Policy.
- **Preview/QA** – disable HSTS by setting `strict_transport_security=False` to avoid forcing HTTPS
  on staging domains.
- **Local development** – set `content_security_policy=None` to relax restrictions when using
  self-hosted developer tools.

Leverage environment variables or configuration management to feed different
`SecurityHeadersSettings` into `register_fastapi` per environment.

## Observability

- Expose the `/security-headers/health` route to your monitoring system; the payload lists missing
  headers so you can alert on policy drift.
- Add a synthetic check that hits a representative endpoint and asserts that the headers returned by
  the module match your baseline.
- For NestJS, wire the `SecurityHeadersService.health()` output into existing readiness endpoints to
  maintain parity with FastAPI deployments.
