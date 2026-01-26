# Passwordless Module Overview

The Passwordless module provides a lightweight scaffold for building magic-link or one-time code
authentication flows. It bundles configuration contracts, template stubs, and test hooks so you can
add production-ready passwordless auth without duplicating boilerplate.

## Key Capabilities

- **Token generation primitives** – The runtime template exposes helpers for generating short-lived
  one-time codes and signing verification payloads.
- **Delivery-agnostic structure** – Keep transport logic (email, SMS, push) out of the module while
  sharing validation logic across backends.
- **NestJS and FastAPI parity** – TypeScript artefacts mirror the Python runtime to support hybrid
  stacks.
- **Repository tests** – Smoke tests assert that token helpers behave deterministically and that the
  generator renders the expected files across variants.

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: document configuration boundaries and expected trust assumptions.
- Threat model: consider abuse cases (rate limiting, replay, injection) relevant to your
  environment.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
