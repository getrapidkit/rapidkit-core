# Session Module Troubleshooting

## Invalid Signature

**Symptom**: `verify_session()` returns `None` for every token.

**Fix**: Confirm the signing key matches the one used when issuing the session. If you recently
rotated keys, allow a grace period where verification checks old keys as well.

## Token Expired

**Symptom**: Requests fail with `401` after long idle periods.

**Fix**: Increase `ttl_seconds` or implement rolling expiration by re-issuing tokens via
`refresh_session()` on successful requests.

## Clock Skew

**Symptom**: Sessions expire immediately on some servers.

**Fix**: Synchronise system clocks (for example with NTP) or set `leeway_seconds` to tolerate minor
clock drift.
