# RapidKit Licensing Overview

RapidKit uses a dual-licensing model to balance an open-source community ecosystem with commercial
offerings for teams that need access to premium capabilities.

## Distribution Tiers

| Tier                              | Contents                                                                                                   | License                                            |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| **Community**                     | Open-source engine bundle, standard starter kits (one per framework), community documentation, CLI tooling | [MIT License](../../LICENSE)                       |
| **Commercial (Pro / Enterprise)** | RapidKit Core engine, premium automation, paid marketplace modules, advanced tooling, internal playbooks   | RapidKit Commercial License (shipped to customers) |

## How to Use

- **Community users** can clone the public repository or download the packaged bundle. You are free
  to use, modify, and redistribute the code under the terms of the MIT License. Please keep the
  copyright notice and license text intact.
- **Commercial customers** receive access credentials for the RapidKit Core engine and premium
  modules. Usage is governed by the commercial license. Redistribution of the commercial source code
  or templates is prohibited unless expressly allowed in your contract.

## Licenses Inside the Repository

- `LICENSE` — MIT license text packaged with community distributions.
- `LICENSE_COMMERCIAL.md` — The EULA for RapidKit Core and other commercial assets (internal only;
  not shipped to the community bundle).
- `licenses/kits/*.json` — Metadata describing the license that applies to each kit. RapidKit
  maintains exactly one **standard** kit per framework:
  - `fastapi.standard.json` — MIT for the FastAPI standard kit.
  - `nestjs.standard.json` — Apache-2.0 for the NestJS standard kit.

## Standard Kits & Framework Support

- Each supported framework ships with exactly one curated **standard kit** that is distributed with
  the community bundle under an open-source license.
- Additional paid or experimental kits, when available, remain part of the commercial offering and
  inherit the RapidKit Commercial License.
- Framework roadmap updates are tracked by the maintainers; licensing metadata must be updated
  alongside any new kit delivery before community packaging.

## Adding New Kits or Modules

When authoring a new kit or module, include a licensing metadata file under `licenses/kits/` or
`licenses/modules/` and update the distribution maps so the correct files ship with each tier.
Ensure sensitive or commercial-only artifacts are explicitly excluded in the relevant `*_map.yml`
file.

## Module Marketplace & Community Contributions

- Modules can be published by RapidKit or community contributors. Authors may choose to release
  modules for free (MIT/Apache-2.0) or monetize them through the RapidKit Marketplace.
- Paid modules **must** provide licensing metadata in `licenses/modules/<module>.json`, declare
  entitlements in their manifest, and list "marketplace" as the distribution channel.
- Community-contributed modules that remain free should still provide SPDX-compatible license
  identifiers and adhere to the manifest schema outlined in `docs/modules/overview.md`.
- Marketplace onboarding guidelines (pricing, revenue share, support expectations) are maintained
  internally; public contributors should reference the community guidelines in
  `docs/contributing/CONTRIBUTING.md`.

## Questions & Contact

Need clarification or a commercial license? Contact the RapidKit licensing team at
`licensing@getrapidkit.com`.
