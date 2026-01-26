# Users Core Module Overview

The Users Core module supplies foundational user management primitives for RapidKit services. It
ships domain models, DTOs, service facades, and repository contracts alongside framework adapters
for FastAPI and NestJS so teams can bootstrap consistent user flows quickly.

## Key Capabilities

- **Canonical domain model** – Pydantic DTOs and dataclasses capture identity, profile, and status
  information with validation ready for transport layers.
- **Service orchestration** – `UsersService` centralises lifecycle operations (create, retrieve,
  update, search) while the facade exposes task-focused helpers for endpoints and jobs.
- **Repository abstraction** – A protocol defines persistence operations; the provided in-memory
  implementation enables local development and testing without extra dependencies.
- **Framework adapters** – FastAPI dependency providers and routers plus NestJS providers expose the
  service layer to HTTP handlers with minimal glue.
- **Health telemetry** – `/api/health/module/users-core` validates configuration and reports service
  readiness via the shared health registry.

See the usage guide for installation steps, advanced guide for custom persistence patterns, and the
troubleshooting page for common integration issues.

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: document configuration boundaries and expected trust assumptions.
- Threat model: consider abuse cases (rate limiting, replay, injection) relevant to your
  environment.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
