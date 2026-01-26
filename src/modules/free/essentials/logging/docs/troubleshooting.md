# Logging Module Troubleshooting

This page lists common issues encountered when adopting the RapidKit logging module and how to
resolve them.

## Missing Vendor Payload

**Symptoms:** Runtime errors indicating that the vendor logging file is missing.

**Resolution:** Ensure `rapidkit modules install logging` (or `rapidkit add module logging`) ran
successfully. The wrapper expects
`.rapidkit/vendor/logging/<version>/src/modules/free/essentials/logging/logging.py` to exist.
Regenerate the artefacts and commit the vendor snapshot.

## Queue Listener Not Starting

**Symptoms:** `RuntimeError: Queue listener not initialised` when calling `create_queue_handler`.

**Resolution:** Make sure `LOG_ASYNC_QUEUE` or `RAPIDKIT_LOGGING_FORCE_ASYNC_QUEUE` is set to
`true`. The queue listener spins up lazily when `setup_queue_listeners` is invoked, so ensure the
first logger is retrieved after the environment is configured.

## Missing Request Context

**Symptoms:** `request_id`/`user_id` fields remain `null` in logs.

**Resolution:** Verify that the FastAPI middleware is registered, or that overrides did not disable
request context propagation. Manually call `set_request_context` when running outside HTTP request
scopes.

## OpenTelemetry / Metrics Handlers Inactive

**Symptoms:** Expected bridge handlers are not attached even after enabling environment variables.

**Resolution:** The current implementation provides stubs. Enable them via overrides, then implement
the handler logic to forward records to your telemetry stack.

## Extra Snippet Not Copied

**Symptoms:** `RAPIDKIT_LOGGING_EXTRA_SNIPPET` is set but files are not present in the target
project.

**Resolution:** Ensure the snippet path is either absolute or relative to the module directory.
Optionally set `RAPIDKIT_LOGGING_EXTRA_SNIPPET_DEST` to control the destination. The generator
raises an explicit error if the source file cannot be found.
