# OAuth Module Overview

The OAuth module scaffolds everything required to integrate third-party identity providers into a
RapidKit project. It ships configuration contracts, reusable router scaffolding, and cross-framework
artifacts so teams can wire authentication flows without rebuilding the boilerplate each time.

## Key Capabilities

- **Provider registry scaffold** – Provides strongly typed configuration objects for OAuth providers
  with sensible defaults that live in `templates/base/oauth.py.j2`.
- **FastAPI router stub** – Generates a `create_router()` helper that exposes a ready-to-customise
  `/oauth/health` endpoint and a placeholder callback route.
- **NestJS service scaffold** – Mirrors the Python structure to keep hybrid stacks consistent.
- **Vendor artefacts** – Deposits baseline runtime code under `.rapidkit/vendor/oauth/<version>` so
  updates can be audited across upgrades.

All generated files are designed to be edited safely; rerunning the generator will only overwrite
files that still match the managed templates.

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: document configuration boundaries and expected trust assumptions.
- Threat model: consider abuse cases (rate limiting, replay, injection) relevant to your
  environment.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
