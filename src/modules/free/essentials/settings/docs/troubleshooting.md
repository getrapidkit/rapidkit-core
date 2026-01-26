# Settings Module Troubleshooting

Consult this guide when the generated module misbehaves. Pair it with the migration checklist to
ensure your project matches the lean spec layout.

## Overrides not loading

- Confirm `apply_module_overrides(Settings, "settings")` executes during module import (before the
  application starts).
- Verify that `overrides.py` is in the Python path; FastAPI projects should ensure the package is
  discoverable via `__init__.py`.
- Check `RAPIDKIT_SETTINGS_EXTRA_DOTENV` and `RAPIDKIT_SETTINGS_RELAXED_ENVS` for typos—values are
  comma-separated without spaces.
- Enable debug logging by setting `RAPIDKIT_SETTINGS_LOG_REFRESH=1`; the refresh log lists
  registered override hooks.
- From v1.0.23 onwards the module logs an actionable warning if `pydantic_settings` is missing while
  `RAPIDKIT_SETTINGS_EXTRA_DOTENV` is set—install the package to enable custom dotenv files.

## Production guard failures

- Ensure the deployment sets `APP_ENV=prod`. Missing or mismatched values default to strict mode.
- Use `RAPIDKIT_SETTINGS_RELAXED_ENVS="dev,ci"` to bypass the guard outside production.
- Inspect the stack trace for missing secrets; regenerate `.env.sample` files to match new fields.

## Telemetry not emitting

- Set `RAPIDKIT_SETTINGS_TELEMETRY_ENDPOINT` or the service-specific variables expected by your
  exporter.
- Check network connectivity—observability hooks run in the refresh thread, so failures are logged
  but not retried unless you add retry logic.
- For NestJS, make sure `SettingsTelemetryModule` is imported in the root module so DI wires the
  transport.

## Generator failures

- Run `python src/modules/free/core/settings/generate.py fastapi /tmp/out` to print debug
  information about the generation process.
- Ensure the requested framework is supported; use `python generate.py --help` to list available
  frameworks.
- Delete stale `.rapidkit/vendor/settings` snapshots when switching versions to avoid checksum
  mismatches.

## Hot reload not triggering

- Verify `HOT_RELOAD_ENV_ALLOWLIST` contains the active environment (for example `dev` or `local`).
- Ensure `watchfiles` or `watchdog` dependencies are installed in the running environment.
- Confirm the service mounts the config directory; containerised deployments often miss volume
  mounts for local files.

## Requirement validation failures

- `validate_requirements()` now blocks generation when dependencies are missing. Ensure the required
  Python or Node.js toolchains (FastAPI, npm, etc.) are installed before running the generator in
  CI. Use the error context emitted by `generate.py` to pinpoint missing binaries or packages.
- When extending the module with a custom framework, expose your plugin through the
  `rapidkit.settings.plugins` entry point so discovery works without editing the registry.
- Pre-generation hooks run automatically. Keep them idempotent—each invocation should leave the
  project tree in a consistent state to avoid flaky pipelines when the generator executes multiple
  times (e.g. pre-commit + CI).
