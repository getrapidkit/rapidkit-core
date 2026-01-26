# Auth Core Module Overview

The Auth Core module standardises authentication primitives across RapidKit projects. It provides
password hashing, token issuance, health telemetry, and framework adapters for FastAPI and NestJS.

## Key Capabilities

- **Deterministic hashing** – PBKDF2 helpers with configurable policy enforcement.
- **Token signing** – HMAC (HS256) tokens with issuer, audience, and scope support.
- **Dependency injection** – Cached runtimes and helper functions for FastAPI routes.
- **Health endpoints** – `/api/health/module/auth-core` surfaces pepper configuration and hashing
  metadata.
- **Cross-framework support** – NestJS providers mirror the Python runtime for hybrid stacks.

Refer to the usage and troubleshooting guides for detailed integration steps.

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: document configuration boundaries and expected trust assumptions.
- Threat model: consider abuse cases (rate limiting, replay, injection) relevant to your
  environment.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
