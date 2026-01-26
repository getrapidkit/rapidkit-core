# Deployment Module Troubleshooting

Common issues and remediation steps for the deployment module.

## Generator Fails with Missing Template

- Ensure `module.yaml` still references existing templates in `templates/base/` or
  `templates/variants/<framework>/`.
- Run `poetry run python scripts/check_module_integrity.py --module deployment` to detect missing
  files.

## CI Workflow Not Generated

- Confirm `include_ci` is `true` in `module.yaml` or unset `RAPIDKIT_DEPLOYMENT_SKIP_CI` before
  running the generator.
- For temporary suppression, export `RAPIDKIT_DEPLOYMENT_SKIP_CI=1` and rerun generation.

## Docker Build Uses Wrong Runtime

- Check `options.python_version` and `options.node_version` in `module.yaml`.
- Override at runtime with `RAPIDKIT_DEPLOYMENT_FORCE_RUNTIME=python` or `node`.

## Postgres Service Missing

- Confirm `include_postgres` is `true` in `module.yaml`.
- Set `RAPIDKIT_DEPLOYMENT_INCLUDE_POSTGRES=1` before running the generator to force enablement.
