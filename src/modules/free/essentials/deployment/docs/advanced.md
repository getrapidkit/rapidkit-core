# Deployment Module Advanced Scenarios

This document captures advanced configuration patterns and integration guidance for the deployment
module.

## Custom Workflow Augmentation

Set `RAPIDKIT_DEPLOYMENT_EXTRA_WORKFLOW` to the path of an additional workflow template. The
override contract appends that template into `.github/workflows` after the standard CI pipeline is
rendered.

### Override hooks

`DeploymentOverrides` implements four hook points surfaced by `BaseModuleGenerator`:

- `apply_base_context` mutates global flags such as `include_ci` and `include_postgres`.
- `apply_variant_context_pre` and `apply_variant_context_post` let you tailor per-framework context
  (for example enforcing a runtime or injecting feature flags) before and after the plugin
  enrichments run.
- `post_variant_generation` executes after the variant files land on disk and is the right place to
  render auxiliary workflows, append documentation, or clean up temporary files.

Each hook receives the current context and should return a new mapping; avoid mutating the input
in-place so that tests can track differences safely. When an override needs external resources (for
example reading companion manifests) it can rely on the `module_root` passed to the constructor.

### Environment toggles

The built-in overrides honour several environment variables so CI pipelines can adjust behaviour
without editing `module.yaml`:

| Environment variable                                     | Effect                                                            |
| -------------------------------------------------------- | ----------------------------------------------------------------- |
| `RAPIDKIT_DEPLOYMENT_SKIP_CI=1`                          | Skips rendering the primary CI workflow.                          |
| `RAPIDKIT_DEPLOYMENT_INCLUDE_POSTGRES=1`                 | Adds the Postgres service to Docker Compose and the Makefile.     |
| \`RAPIDKIT_DEPLOYMENT_FORCE_RUNTIME=python               | node\`                                                            |
| `RAPIDKIT_DEPLOYMENT_EXTRA_WORKFLOW=path/to/workflow.j2` | Injects an additional GitHub Actions template after the main run. |

All variables are normalised through `OverrideState`, which makes it easy to monkeypatch that state
inside tests instead of touching real environment variables.

## Alternative Package Managers

The module defaults to `npm`. Switch to `pnpm` or `yarn` by updating `options.package_manager` in
`module.yaml`. The generator derives the correct CLI command via `package_manager_command`.

## Feature Flags via Snippets

The generator pipes context through the shared snippet registry. Register a snippet under the
`deployment` target to inject additional steps, environment variables, or documentation into the
rendered files without editing upstream templates.

## Extending Plugins

Create a new `FrameworkPlugin` subclass, register it in `frameworks/__init__.py`, and mirror the
existing FastAPI or NestJS implementation. Provide accompanying templates under
`templates/variants/<framework>/` and vendor assets if the module should export snapshots.
