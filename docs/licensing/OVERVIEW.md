# RapidKit Licensing Overview

Last updated: 2026-06-04

RapidKit Core is published as a community-first engine. The free module catalog and public kits are
intended to be usable by open-source users and by Workspai product workflows.

## Current Distribution

| Area                                   | License model                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------------ |
| Public core package                    | MIT, unless a file states otherwise.                                           |
| Free modules                           | Open-source module metadata and templates shipped with community distribution. |
| Public kits                            | Kit license metadata under `licenses/kits/`.                                   |
| Internal playbooks and release tooling | Maintainer-only unless included by distribution maps.                          |
| Finished marketplace products          | Product-specific license and delivery terms.                                   |

## Free-First Policy

The current core strategy is to keep framework primitives and backend building blocks free.
Commercial value should come from completed product workspaces, private delivery, support, reviews,
and marketplace operations rather than artificially hiding foundational modules.

## Repository License Files

- `LICENSE` - public package license.
- `licenses/kits/*.json` - kit-level license metadata.
- `licenses/modules/*.json` - module-level metadata when applicable.

## Generated Projects

Generated projects inherit the license terms of the templates and dependencies used to create them.
Product workspaces may add separate license files for commercial delivery.

## Distribution Guardrail

Before publishing, run:

```bash
make community-dist-install
./dev-engine/validate_ai_security.sh
```

No public package should include secrets, private local paths, internal-only release logic, or
commercial customer assets.
