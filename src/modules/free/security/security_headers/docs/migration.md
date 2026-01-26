# Migration

This document tracks behavioural changes across Security Headers releases and outlines safe upgrade
paths.

## Version 1.0.0

- First stable release. Replaces the scaffolded router stub with fully featured FastAPI middleware
  and NestJS services.
- Introduces typed configurations (`SecurityHeadersConfig`, `SecurityHeadersSettings`) and health
  reporting helpers.
- Adds plugin-based framework registry. Projects upgrading from the initial scaffold should remove
  any direct imports of `register_fastapi_plugin` or `register_nestjs_metadata` in favour of the
  generated adapters.

## Upgrade Checklist

1. Regenerate project artefacts via `rapidkit modules upgrade security_headers`.
1. Replace any manual header logic with the generated middleware to avoid duplicate headers.
1. If you relied on CSP report-only mode, set `content_security_policy_report_only=True` in your
   configuration payload.
1. Run the module-maintainer tests
   (`poetry run pytest tests/modules/free/security/security_headers -q`) and your application tests
   before deploying.
