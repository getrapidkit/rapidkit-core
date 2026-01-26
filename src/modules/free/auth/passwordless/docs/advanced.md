# Passwordless Module Advanced Topics

## Replay Protection

Persist verification payloads with a single-use constraint. The runtime exposes a `mark_verified`
hook; override it to atomically delete tokens from your store after successful verification.

## Rate Limiting

Use the `issue_code` hook to enforce per-identity rate limits. For example, block repeated requests
from the same IP or email address within a configurable window. Because the runtime returns both the
code and token, you can update your data store before dispatching notifications.

## Linking Multiple Channels

If you support email and SMS, extend the configuration dataclass with a `channel` enum and capture
metadata for each request. The verification payload already supports arbitrary metadata via the
`context` field.

## Analytics Hooks

Emit structured telemetry when codes are issued and redeemed. The runtime calls `on_issued` and
`on_verified` callbacks if they are provided, making it easy to plug into your observability stack.
