# Module and Kit Compatibility

Last updated: 2026-06-04

RapidKit currently ships 52 stable free modules and three release kit profiles:

- `fastapi.standard`
- `fastapi.ddd`
- `nestjs.standard`

Compatibility is not a static promise written by hand. It is release evidence produced by
stabilization gates and stored under `dev-engine/audit-history/`.

## Current Compatibility Policy

| Evidence                                   | Meaning                                                               |
| ------------------------------------------ | --------------------------------------------------------------------- |
| `make stabilize-fast <category>` passes    | Each module in the category installs in isolated cached kit projects. |
| `make stabilize-shared <category>` passes  | The category composes in a shared project per kit.                    |
| `make stabilize-release <category>` passes | The category has both isolated and shared confidence.                 |
| `make stabilize-release-all` passes        | Full catalog confidence for the current checkout.                     |

## Catalog Snapshot

| Category        | Modules                                                                                                                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ai`            | `agent_runtime`, `ai_assistant`, `ai_guardrails`, `llm_gateway`, `prompt_ops`, `rag_pipeline`, `tool_registry`, `vector_store`                                                                                           |
| `auth`          | `api_keys`, `core`, `oauth`, `passwordless`, `session`                                                                                                                                                                   |
| `billing`       | `cart`, `inventory`, `stripe_payment`, `usage_billing`                                                                                                                                                                   |
| `business`      | `admin_console`, `approval_engine`, `connector_hub`, `connector_pack_library`, `document_pipeline`, `feature_flags`, `forms_engine`, `media_pipeline`, `multi_tenancy`, `org_admin_console`, `storage`, `support_center` |
| `cache`         | `redis`                                                                                                                                                                                                                  |
| `communication` | `email`, `notifications`, `webhook_platform`                                                                                                                                                                             |
| `database`      | `db_mongo`, `db_postgres`, `db_sqlite`                                                                                                                                                                                   |
| `essentials`    | `deployment`, `logging`, `middleware`, `settings`                                                                                                                                                                        |
| `observability` | `analytics_dashboard`, `core`                                                                                                                                                                                            |
| `security`      | `audit_policy`, `cors`, `rate_limiting`, `security_headers`                                                                                                                                                              |
| `tasks`         | `celery`, `event_bus`, `queue_platform`, `workflow_engine`                                                                                                                                                               |
| `users`         | `users_core`, `users_profiles`                                                                                                                                                                                           |

## Updating This Matrix

1. Run the relevant stabilization command.
1. Keep the generated report under `dev-engine/audit-history/`.
1. Update this file only if the module catalog or release kit list changes.

Do not list a module as supported for a kit unless current audit evidence exists.
