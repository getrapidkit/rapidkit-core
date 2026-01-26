# Auth Core Troubleshooting

Common issues and remediation steps when integrating the Auth Core module.

## Missing Pepper Warning

**Symptom**: Application logs include `Auth Core pepper env 'RAPIDKIT_AUTH_CORE_PEPPER' missing`.

**Fix**:

1. Generate a strong pepper: `openssl rand -base64 48`.
1. Add it to your environment (`.env`, secrets manager, or container secret). Example:

```bash
RAPIDKIT_AUTH_CORE_PEPPER="<base64-secret>"
```

3. Restart the application so the dependency helpers can pick up the new value.

## Token Verification Fails After Configuration Changes

**Symptom**: `ValueError("Token signature verification failed")` when verifying tokens.

**Fix**:

- Ensure all services share the same `RAPIDKIT_AUTH_CORE_PEPPER` value.
- If you changed `AUTH_HASH_NAME` or `AUTH_TOKEN_BYTES` in settings, redeploy all instances to avoid
  signature skew.
- Re-issue tokens after modifying cryptographic settings; legacy tokens signed with the previous
  configuration will fail to verify.

## Passwords Rejected Unexpectedly

**Symptom**: `ValueError("Password does not satisfy configured policy requirements")` during
registration.

**Fix**:

- Review the injected settings fields (`AUTH_PASSWORD_MIN_LENGTH`, `AUTH_PASSWORD_REQUIRE_*`).
- Confirm that environment overrides or `.env` values match product requirements.
- Adjust the values and restart the application; the runtime pulls them from the cached settings
  instance.

## Health Endpoint Returns 503

**Symptom**: GET `/api/health/module/auth-core` responds with HTTP 503.

**Fix**:

- Check application logs for the underlying exception. Common causes: missing pepper or invalid YAML
  configuration injected via overrides.
- Validate that `AUTH_HASH_ITERATIONS` and related fields are positive integers.
- Ensure dependent modules (FastAPI, Pydantic) are installed in the runtime environment.

## Regenerating Templates After Upgrades

If you update the module version or adjust overrides:

```bash
rapidkit modules lock --overwrite
rapidkit modules apply auth_core --no-dry-run
poetry run pytest tests/modules/free_auth_core -q
```

This refreshes vendor artefacts, replays snippet injections, and validates the integration tests.
