# Troubleshooting

Catalogue common issues and diagnostics for api keys.

## Diagnostics

- Confirm the health endpoint responds:

```bash
curl -s http://localhost:8000/api_keys/health
```

- If verification fails unexpectedly, ensure the pepper is configured (either explicitly in config
  or via the configured pepper env var).
- If requests fail with configuration errors, re-check `config/api_keys.yaml` and any
  `RAPIDKIT_API_KEYS_*` overrides.

## Common issues

- **"Pepper must be configured"**: set the pepper env var referenced by the runtime config (see
  `RAPIDKIT_API_KEYS_PEPPER_ENV`).
- **Scope mismatch**: ensure the requested scopes are included in `RAPIDKIT_API_KEYS_ALLOWED_SCOPES`
  (or the default config).
