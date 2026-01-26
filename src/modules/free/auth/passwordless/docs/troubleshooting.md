# Passwordless Module Troubleshooting

## Codes Expire Unexpectedly

**Symptom**: Users report that magic links no longer work after a short delay.

**Fix**: Increase `ttl_seconds` when instantiating `PasswordlessRuntime`. Ensure background workers
that clean stale tokens respect the same TTL.

## Duplicate Code Delivery

**Symptom**: Users receive multiple codes in quick succession.

**Fix**: Add rate limiting to the `issue_code` hook and ensure your transport provider deduplicates
based on message idempotency keys.

## Verification Always Fails

**Symptom**: `verify_code()` returns `False` even for fresh codes.

**Fix**: Confirm the persistence layer stores both the code and token exactly as returned by the
runtime. Normalise casing and remove whitespace before comparison.

## Brute Force Attempts

**Symptom**: Logs show repeated failed verification attempts from the same IP.

**Fix**: Track failure counts and block the offending identifier temporarily. Because the runtime
returns the candidate identifier, you can implement IP and identity throttling without modifying the
module itself.
