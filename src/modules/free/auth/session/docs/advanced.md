# Session Module Advanced Topics

## Key Rotation

Rotate signing keys without forcing every session to expire immediately by introducing a key set.
Augment the runtime with a `KeyResolver` that exposes `current_key()` and `legacy_keys()`. Attempt
verification against legacy keys before rejecting a token and re-sign using the active key on
successful validation.

## Stateful Backends

When using Redis or another external store, override the session repository interface to persist
issued tokens. Leverage TTL features in the backing store instead of relying solely on JWT expiry.

## Auditing

The runtime attaches issue and expiry timestamps to every payload. Emit structured logs or metrics
in the verification hook to build insights about session lifecycles. This makes it easier to detect
compromised tokens or unusual refresh patterns.
