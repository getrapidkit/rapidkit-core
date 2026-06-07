# RapidKit Community Distribution Guide

Last updated: 2026-06-04

This guide explains how to build, verify, and install the public RapidKit community distribution
from the core repository.

## Package Model

- PyPI distribution: `rapidkit-core`
- Python entry points: `rapidkit`, `rkc`
- npm wrapper package: `rapidkit`
- Stable public repository: `https://github.com/rapidkitlabs/rapidkit-core`
- Staging repository: `https://github.com/rapidkitlabs/community-staging`

The npm wrapper is the recommended public onboarding path. The Python package is the engine used by
the wrapper and by maintainers.

## Main Verification Command

```bash
make community-dist-install
```

This command:

1. Builds the community distribution into `dist-community/community`.
1. Finalizes distribution metadata.
1. Regenerates `poetry.lock` for the generated package.
1. Creates a clean `.community-venv`.
1. Installs the generated package.
1. Verifies community-only command boundaries.

## Network Mirrors and Proxies

The official path uses PyPI. If your network cannot reach PyPI, you may set a temporary mirror:

```bash
RAPIDKIT_PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple make community-dist-install
```

Rules:

- mirrors are environment-level fallbacks
- do not commit mirror URLs into generated package metadata
- do not document a private/local proxy as a public requirement
- unset `RAPIDKIT_PYPI_MIRROR` when returning to official PyPI

## Release Gates

Before publishing:

```bash
python scripts/check_version_alignment.py
make stabilize-release-all
make community-dist-install
./dev-engine/validate_ai_security.sh
```

Recommended evidence location:

```text
dev-engine/audit-history/distribution/
dev-engine/audit-history/security/
```

## Manual Build

```bash
poetry build
twine check dist/*
```

Publishing should be performed by release automation or a controlled maintainer workflow with PyPI
tokens stored as secrets.

## CLI Ownership

The Python package owns engine commands and project-level runtime delegation. The npm wrapper owns
workspace/product/share/contract workflows and bridges to the installed Python engine when needed.

If a user accidentally invokes a wrapper-owned command through the Python entrypoint, the Python CLI
should return actionable guidance rather than trying to reimplement the npm behavior.

## Public Distribution Blockers

Do not publish if:

- distribution maps leak internal-only files
- generated pyproject or docs contain local paths
- `poetry.lock` cannot be regenerated
- package install requires manual patching
- internal/admin-only commands are visible in community help
- security validation fails

## Related Docs

- `dev-engine/playbooks/distribution/distribution-test-prompt.md`
- `dev-engine/playbooks/distribution/ai-security-prompt.md`
- `docs/internal/deployment/tokens-and-secrets.md`
- `docs/internal/deployment/release-model-a-policy.md`
