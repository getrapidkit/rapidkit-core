# Usage

This guide walks through generating the module, registering the FastAPI adapter, and customising
header policies.

## Quickstart

1. Install the module for your target framework:

   ```bash
   rapidkit modules add security_headers --framework fastapi
   ```

1. Apply the generated FastAPI wrapper in your application entrypoint:

   ```python
   from fastapi import FastAPI

   from src.modules.free.security.security_headers.security_headers import (
       SecurityHeadersSettings,
       register_fastapi,
   )

   app = FastAPI()

   register_fastapi(
       app,
       config=SecurityHeadersSettings(
           content_security_policy="default-src 'self'; img-src 'self' data:; object-src 'none'",
           permissions_policy={"geolocation": [], "camera": []},
       ),
   )
   ```

1. Run your application and inspect any response headers. You should see values similar to:

   ```http
   Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   Referrer-Policy: strict-origin-when-cross-origin
   ```

## Configuration Reference

`SecurityHeadersSettings` mirrors the runtime dataclass and exposes the following notable fields:

| Field                          | Type             | Default         | Description                                                     |
| ------------------------------ | ---------------- | --------------- | --------------------------------------------------------------- |
| `content_security_policy`      | \`str            | None\`          | `None`                                                          |
| `permissions_policy`           | \`dict\[str, str | list\[str\]\]\` | `{}`                                                            |
| `cross_origin_embedder_policy` | \`str            | None\`          | `"require-corp"`                                                |
| `additional_headers`           | `dict[str, str]` | `{}`            | Arbitrary name/value pairs appended to the computed header set. |

`strict_transport_security` and `x_xss_protection` remain boolean toggles, while
`x_content_type_options` accepts either `false` or the literal header token (default: `"nosniff"`).
This keeps the protection enabled by default while letting you supply a custom directive when
necessary.

## Retrieving Health Information

The FastAPI router exposes a `/security-headers/health` endpoint that returns:

```json
{
  "module": "security_headers",
  "status": "ok",
  "metrics": {
      "enabled": true,
      "header_count": 8,
      "missing": []
  }
}
```

Use this payload for monitoring dashboards or automated compliance checks.
