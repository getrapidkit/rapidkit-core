# ⚙️ RapidKit GitHub Actions Overview

This guide explains how the `.github` directory in the core repository orchestrates CI,
distribution, release automation, and downstream community deployments. Use it as the single
reference for triggers, responsibilities, and how reusable workflows wire everything together.

> ✅ **Audience**: Maintainers and contributors who need to understand or extend the automation stack
> before touching any workflow files.

______________________________________________________________________

## 📂 Directory Topology

```text
.github/
├── CODEOWNERS / ISSUE_TEMPLATE/ / PULL_REQUEST_TEMPLATE.md
├── copilot-instructions.md
├── codeowners-config/           # Shared CODEOWNERS fragments for generated repos
├── config/
│   └── tiers.yml                # Tier metadata consumed by composite actions
├── distribution/                # Docs & helpers bundled into downstream repos
├── actions/
│   ├── setup-distribution/      # Builds tier-specific dist payloads
│   └── push-distribution/       # Clones + syncs community repositories
└── workflows/
  ├── *.yml (core CI, automation, release)
  ├── docker-build.yml / python-*.yml  # Reusable workflows callable across repos
  └── distribution/
    └── community-*.yml      # Entry points copied into community repos
```

- **Local edits** happen in `core/.github/**`. Downstream repositories only receive generated
  workflow files via `sync-distribution.yml` + `deploy-workflows.yml`.
- The two composite actions are the foundation for distro publishing; reusable workflows now live at
  the top level of `.github/workflows/` so downstream repos can call them via
  `Baziar/core/.github/workflows/<file>@ref` without copying extra files.

______________________________________________________________________

## 🗂️ Workflow Catalog

### 1. Quality & Safety Gates

| File                                                    | Trigger         | What it enforces                                      | Notes                                                                      |
| ------------------------------------------------------- | --------------- | ----------------------------------------------------- | -------------------------------------------------------------------------- |
| `ci.yml` / `core-ci.yml`                                | push / PR       | Lint + test matrix for kits + modules                 | `core-ci` runs only against change-detected paths to keep PR feedback fast |
| `coverage.yml`                                          | push to main    | Uploads full coverage reports                         | Publishes `coverage.xml` and HTML artifacts                                |
| `bootstrap-python.yml`                                  | workflow_call   | Pre-baked Python env job reused across workflows      | Saves repeated setup logic                                                 |
| `commit-message-check.yml`                              | pull_request    | Conventional commit & Jira tag enforcement            | Fails early before other jobs start                                        |
| `commit-standards.yml`                                  | schedule + PR   | Runs `scripts/check_commits.py` for deeper validation | Adds branch protection hook                                                |
| `markdown-check.yml`                                    | pull_request    | Vale/markdownlint for docs                            | Blocks doc regressions                                                     |
| `secured-rapidkit-modules.yml`                          | schedule/manual | Runs security scanners on modules                     | Paired with `scheduled-validation.yml` for compliance                      |
| `modules-outdated.yml` / `auto-update-modules-lock.yml` | schedule/manual | Detects and optionally bumps module locks             | Keeps templates fresh                                                      |
| `scheduled-validation.yml`                              | nightly         | Smoke-tests kits + modules                            | Uses same matrix as community CI                                           |

### 2. Distribution & Repo Sync

| File                                     | Trigger                           | Outcome                                                                                |
| ---------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------- |
| `sync-distribution.yml`                  | manual / push to main             | Runs `setup-distribution` + `push-distribution` for every tier defined in input matrix |
| `promotion-community.yml`                | manual                            | Promotes the staging tier output to the public community repo once guard checks pass   |
| `deploy-workflows.yml`                   | manual                            | Copies latest workflow files into downstream repos without touching product files      |
| `distribution/community-*.yml`           | triggered inside downstream repos | Provide CI, docker, guard, publishing, and release automation that mirror core         |
| `distribution/community-<staging>-*.yml` | triggered inside staging repo     | Same as above but pointing at staging artifacts                                        |

Key reusable foundations inside `workflows/distribution/`:

| File                 | Used by (via `Baziar/core/.github/workflows/<file>@ref`)              | Description                                                              |
| -------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `docker-build.yml`   | `community-docker.yml`, staging docker workflow, `docker-publish.yml` | Multi-arch Docker build/push with provenance attestations                |
| `python-publish.yml` | `community-publish.yml`, `publish.yml`                                | Standard PyPI/TestPyPI publishing routine                                |
| `python-release.yml` | `community-release.yml`, `release.yml`                                | Builds release bundles, uploads artifacts, and hands off to PyPI publish |

### 3. Release Automation

| File                    | Trigger           | Highlights                                                             | Notes                                              |
| ----------------------- | ----------------- | ---------------------------------------------------------------------- | -------------------------------------------------- |
| `release.yml`           | tag push `v*`     | Builds kits, uploads release assets, delegates to `python-release.yml` | Publishes artifacts & attaches SBOM                |
| `release-please.yml`    | push to main      | Generates/updates release PRs + tags using Release Please              | Requires GitHub Actions PR permissions             |
| `release-pr-upkeep.yml` | schedule          | Rebases Release Please PRs to keep them mergeable                      | Keeps automations green without manual babysitting |
| `publish.yml`           | workflow_dispatch | Manual PyPI publish via `python-publish.yml`                           | Accepts TestPyPI/PyPI target inputs                |
| `docker-publish.yml`    | workflow_dispatch | Builds & pushes docker images via reusable docker workflow             | Multi-arch ARM64/AMD64 build                       |

### 4. Support & Utility

| File                                                                                  | Trigger       | Purpose                                             |
| ------------------------------------------------------------------------------------- | ------------- | --------------------------------------------------- |
| `sync-distribution.yml`                                                               | manual/push   | Already covered; centerpiece for tier sync          |
| `deploy-workflows.yml`                                                                | manual        | Ensures downstream `.github/workflows` stay current |
| `promotion-community.yml`                                                             | manual        | Moves staging artifacts to community                |
| `sync-distribution.yml` + `promotion-community.yml` + `deploy-workflows.yml` together | release train | Provide "core ➜ staging ➜ community" pipeline       |

______________________________________________________________________

## 🧱 Composite Actions

### `setup-distribution`

- Reads `.github/config/tiers.yml` to discover repo metadata and licensing.
- Scans `src/modules/**/module.yaml` and `src/kits/**/kit.yaml` to remove content above the
  requested tier.
- Copies files based on `root_files_map.yml`, creates `.rapidkit/source.json`, and stages docs/tests
  for the tier.

### `push-distribution`

- Clones (or auto-creates) `baziar/community*` repositories with the provided token.
- Preserves the target repo's `.github` (excluding workflows) to keep CODEOWNERS/templates intact.
- Injects tier-specific workflow templates from `.github/workflows/distribution/`.
- Writes provenance metadata so downstream repos know which core commit produced the sync.

> ℹ️ These composite actions intentionally avoid Git history rewriting. Each tier repository keeps
> its own linear history even though the source of truth lives in `core`.

______________________________________________________________________

## 🔁 Lifecycle: Core ➜ Staging ➜ Community

1. **Core CI (`ci.yml` / `core-ci.yml`)** validates commits.
1. **`sync-distribution.yml`** builds the tiered payloads via the composite actions.
1. **Staging repository** receives updates (default community staging tier).
1. **`promotion-community.yml`** promotes staging SHA to public community once guard checks pass.
1. **Community workflows** (copied from `distribution/community-*.yml`) run inside the community
   repo for extra CI, docker, publish, and release automation.
1. **`deploy-workflows.yml`** can be run at any time to refresh workflow files without shipping
   product changes.

This lifecycle keeps high-risk edits inside the core repo while guaranteeing downstream repos share
identical automation contracts.

______________________________________________________________________

## 🧭 Operating & Troubleshooting

### Run a workflow manually

```bash
# Trigger sync-distribution for both community and staging tiers
gh workflow run sync-distribution.yml \
  -R getrapidkit/core \
  -f tiers="community,<staging>"
```

```bash
# Force docker publish from core using the reusable workflow
gh workflow run docker-publish.yml -R getrapidkit/core
```

- Use `gh run watch --exit-status` to monitor the execution end-to-end.
- All workflows honor change detection where possible; expect skipped jobs when irrelevant files are
  touched.

### Updating downstream workflows

1. Modify files under `.github/workflows/**` in core.
1. Merge the PR after CI succeeds.
1. Run `gh workflow run deploy-workflows.yml -R getrapidkit/core` to push updates into the tier
   repos without waiting for a full distribution sync.

### Common issues

| Symptom                                          | Likely Cause                                         | Fix                                                                                         |
| ------------------------------------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `push-distribution` fails with `Bad credentials` | `API_TOKEN_GITHUB` lacks `repo` + `workflow` scope   | Regenerate PAT and re-run                                                                   |
| Community workflows missing after sync           | `preserve_workflows=false` or templates missing      | Ensure distribution templates exist and rerun sync                                          |
| Release Please cannot create PR                  | Repo settings block GitHub Actions from creating PRs | Enable "Allow GitHub Actions to create and approve pull requests" under repository settings |

______________________________________________________________________

## 🔗 Related Docs

- [`docs/deployment/CI-CD-SIMPLIFICATION.md`](../deployment/CI-CD-SIMPLIFICATION.md) – history of
  the lightweight workflow initiative.
- [`docs/contributing/CONTRIBUTING.md`](../contributing/CONTRIBUTING.md#workflow-deployment) – CLI
  commands for contributors.

If you update or add workflows, ensure this document stays in sync so new maintainers have an
accurate picture of the automation surface.
