# Troubleshooting

Use the following guidance to diagnose issues when the expected headers are missing or
misconfigured.

## Diagnostics

1. Hit the generated health endpoint:
   ```bash
   curl -s http://localhost:8000/security-headers/health | jq
   ```
   Ensure `status` is `ok` and review the `metrics.missing` list for disabled headers.
1. Inspect application state within FastAPI:
   ```pycon
   >>> app.state.security_headers_headers
   {'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload', ...}
   ```
   If the attribute is missing, confirm `register_fastapi` is called before routers are mounted.
1. For NestJS deployments, verify that `SecurityHeadersModule.register()` is imported in your root
   module and that the service is mounted as global middleware.

## Common Issues

| Symptom                        | Resolution                                                                                                                                                         |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Headers missing in development | Ensure the FastAPI middleware is registered in the same application instance used by your tests. If using multiple FastAPI apps, call `register_fastapi` for each. |
| Duplicated headers             | Remove any custom middleware that sets the same header names to avoid conflicting values.                                                                          |
| CSP blocking local assets      | Override `content_security_policy` in development to include `http://localhost:<port>` or disable CSP locally.                                                     |

## Support Channels

If issues persist, collect the health payload, application logs, and the generated configuration
YAML, then open a ticket via <https://github.com/getrapidkit/core/issues> with the details.
