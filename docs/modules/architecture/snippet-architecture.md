# RapidKit Snippet Architecture

This document describes RapidKit’s snippet system end-to-end: how modules declare snippet
injections, how the CLI applies them safely to real projects, and how operators can reconcile,
audit, roll back, and resolve conflicts.

> Scope: This is about *snippet injection orchestration* (registration + application + state). It is
> not a template authoring tutorial.

## Why snippets exist

RapidKit modules often need to modify existing “host” files (for example `src/main.py`, a FastAPI
app bootstrap, a NestJS module registration file, etc.). Re-rendering whole files is brittle and
leads to large diffs. Snippets provide a controlled, traceable way to insert small fragments into
existing files.

## Key concepts

- **Producer module**: The module that ships the snippet (declared in its `config/snippets.yaml` and
  backed by a template in `templates/snippets/`).
- **Target file**: The file in the user project that will be modified.
- **Anchor**: A marker (usually a line or token) that identifies *where* a snippet should be
  inserted.
- **Marker block**: The injected region is wrapped with RapidKit start/end markers so the system can
  re-run safely (idempotent) and also roll back.
- **Owner module (inferred)**: If the target path is under
  `src/modules/<tier>/<category>/<module>/...`, RapidKit infers the owner module slug from the path.
  Owner inference enables safe gating for cross-module injections.

## Where snippets are declared (module side)

A module declares snippets in:

- `src/modules/<tier>/<category>/<module>/config/snippets.yaml`
- Snippet templates live in: `src/modules/<tier>/<category>/<module>/templates/snippets/`

Typical injection-style snippet entries include:

- `id` (stable identifier)
- `template` (filename under `templates/snippets/`)
- `target` (one or more destination paths)
- `anchor` (one or more anchor strings)
- Optional: `profiles`, `features`, `schema`, `conflict_resolution`, `priority`

## Runtime state (project side)

RapidKit maintains two important project-side registries:

- `registry.json`: Installed modules (the project’s truth of “what’s installed”).
- `.rapidkit/snippet_registry.json`: Snippet injection state (the project’s truth of “what was
  injected and what is pending”).

`.rapidkit/snippet_registry.json` is a state machine over snippet keys. Each entry tracks:

- the snippet’s producer module slug
- target file path
- patch mode
- status and timestamps
- errors (when failed/conflicted)

### Statuses

- `pending`: Registered but not yet applied (or needs re-application).
- `applied`: Successfully injected and verified.
- `failed`: Attempted but failed (safe failure; no partial writes).
- `conflicted`: The target file contains malformed/duplicate marker blocks or is otherwise unsafe to
  modify automatically.

## Injection lifecycle

### 1) Install (add module)

When you run:

- `rapidkit add module <slug> --profile <kit>`

RapidKit:

1. Reads module dependencies from `module.yaml` (`depends_on`) and installs prerequisites (or fails
   fast when configured).
1. Registers snippet injections (from `config/snippets.yaml`) into
   `.rapidkit/snippet_registry.json`.
1. Applies snippets to target files using marker blocks and patch modes.
1. Records state transitions (`pending` → `applied` or `failed/conflicted`) in
   `.rapidkit/snippet_registry.json`.

### 2) Reconcile

Reconciliation is a deterministic “make the project converge” operation:

- `rapidkit reconcile`

It attempts to apply all pending snippets that are allowed by the project’s installed module set and
safety rules.

Common uses:

- after installing multiple modules
- after resolving a conflict manually
- after changing a file that contains anchors

### 3) Plan-only (diff without writes)

To preview what reconcile would do, without modifying the project:

- `rapidkit reconcile --plan`

This prints diffs only and guarantees “no writes” to the real project.

### 4) Rollback

To remove a previously injected marker block and return the entry to `pending`:

- `rapidkit rollback snippet --key <snippet_id>::<filename>`

Rollback is marker-based and does not depend on template availability.

### 5) Conflict workflow

If a file contains malformed/duplicate markers, RapidKit marks the snippet as `conflicted` and does
not modify the file.

To unblock reconciliation after you fix the file manually:

- `rapidkit reconcile --resolve-key <key> --resolve-to pending`

This updates registry state only (audited), then you can rerun `rapidkit reconcile`.

## Safety and gating rules

RapidKit is intentionally conservative:

- **No unsafe writes**: On parse/injection errors, snippets become `failed`/`conflicted` with no
  partial modifications.
- **Owner gating**: If a snippet targets a file under `src/modules/<...>/<module>/...`, that owner
  module must be installed (tracked via `registry.json`) before injection is allowed.
- **No auto-create for module-owned targets**: If the owner module isn’t installed or the
  module-owned target file doesn’t exist, RapidKit refuses to create it implicitly.

## Patch modes

Patch mode controls *how* RapidKit edits target files.

- `no_touch`: Only modify marker blocks; do not run formatters (minimizes unrelated diffs).
- `ast_py` (Python targets): Uses a Python CST/AST-aware path with pre/post parse validation. If
  parsing fails, the snippet is marked `conflicted` and no write occurs.

Default behavior:

- For `.py` targets, when `patch_mode` is not explicitly set, RapidKit defaults to `ast_py`.

## Audit trail

RapidKit appends audit events to:

- `.rapidkit/audit/snippet_injections.jsonl`

Events are emitted for reconciliation outcomes, conflict resolutions, and rollbacks.

## Stabilization expectations (module quality)

A “stable” module should satisfy:

- `module.yaml` declares all prerequisites in `depends_on`.
- `config/snippets.yaml` is parseable and references real files under `templates/snippets/`.
- If a snippet injects into another module’s directory (`src/modules/<...>/<other-module>/...`),
  that owner module is in the dependency closure.
- Installing the module into a fresh kit project results in a clean snippet registry (no `pending`,
  `failed`, or `conflicted` entries).

## Troubleshooting

- **Pending snippets**: Run `rapidkit reconcile --verbose`. Check that prerequisites are installed
  and anchors exist.
- **Conflicted snippets**: Fix marker blocks manually, then
  `rapidkit reconcile --resolve-key ... --resolve-to pending` and rerun reconcile.
- **Unexpected diffs**: Use `patch_mode=no_touch` for minimal formatting impact, or rely on `ast_py`
  for Python safety.
