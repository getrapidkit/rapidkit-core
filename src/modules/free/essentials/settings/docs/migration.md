# Migrating to Lean Spec v2

Lean Spec v2 consolidates generator logic, shared overrides, and documentation so every module can
be updated via the RapidKit CLI. Follow the checklist below to move existing projects.

## Prerequisites

- RapidKit CLI `>= 0.12.0`
- Access to the legacy module with `generator.py` and bespoke overrides
- Green test suite for the existing settings implementation

## Migration flow

1. **Snapshot the legacy implementation**

   - Copy the current `settings.py`, custom sources, and overrides into `backups/` for reference.
   - Run `pytest tests/modules/settings -q` to capture a pre-migration baseline.

1. **Adopt the new module layout**

   - Create `module.yaml`, `README.md`, and `templates/variants/<framework>` directories if they do
     not exist.
   - Move hand-written files into templates; replace in-repo copies with generated artifacts.
   - Record entry points in `module.yaml` so the CLI can orchestrate generation.

1. **Port overrides to shared contracts**

   - Replace ad-hoc hooks with implementations in `overrides.py` that call
     `apply_module_overrides(..., "settings")`.
   - Leverage shared helpers such as `_append_extra_dotenv_sources` and
     `_refresh_with_observability`.
   - Remove duplicated exception or versioning utilities in favour of the shared modules.

1. **Regenerate outputs**

   - Run `rapidkit modules add settings --profile <framework>` or execute
     `generate.py <framework> <target-dir>` manually.
   - Commit the regenerated files plus the `.rapidkit/vendor` snapshot.

1. **Validate**

   - Execute `pytest tests/modules/settings -q` and run a smoke test in a sample project.
   - Compare runtime behaviour against your baseline (env files loaded, telemetry emitted,
     production guard enforced).

## Post-migration clean-up

- Remove deprecated scripts (`generator.py`, `versioning.py`) once the new generator is wired.
- Update internal runbooks so teams consume the module through the CLI instead of copying files
  manually.
- Add CI automation to run the generator against a sandbox project to detect template drift.

## Troubleshooting

- **Missing override behaviour** → ensure environment variables (for example
  `RAPIDKIT_SETTINGS_EXTRA_DOTENV`) are reconfigured in deployment manifests.
- **Template rendering errors** → run `python generate.py --debug` to inspect the final Jinja
  context and confirm template names.
- **Version mismatches** → delete `.rapidkit/vendor/settings` and re-run the generator to refresh
  the snapshot.
