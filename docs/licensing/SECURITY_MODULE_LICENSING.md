# RapidKit Module Licensing & Entitlements

## Overview

This document describes how RapidKit unlocks premium capabilities through license-driven
entitlements across both free community modules and paid marketplace offerings. It covers:

- Module categories (community vs. marketplace) and distribution rules
- Required fields in module manifests
- License file structure (`license.json`)
- CLI tooling for inspection and activation
- Enforcement based on module entitlements and feature flags
- Developer workflow and auditing best practices

______________________________________________________________________

## 1. Module Manifest Fields

Each module manifest (`module.yaml`) must include:

```yaml
entitlements:
  modules:
    - billing
  features:
    - usage_metrics
capabilities: [] # Additional metadata used by the CLI for marketing copy
```

- `entitlements.modules`: Identifier(s) that must be present in the active license to install the
  module. Community (free) modules may leave this empty; marketplace modules **must** reference the
  entitlement ID assigned during onboarding.
- `entitlements.features`: Optional fine-grained flags toggled within the module after activation.
- `capabilities`: Human-friendly description of what the module offers.

### Module Categories & Distribution Channels

| Category           | Typical License             | Distribution                                              | Notes                                                                            |
| ------------------ | --------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Community (free)   | MIT / Apache-2.0            | Bundled with the community tier or published in OSS repos | No entitlements required. Authors should still provide SPDX license metadata.    |
| Marketplace (paid) | Commercial (per module)     | RapidKit Marketplace                                      | Requires entitlements, billing integration, and acceptance of marketplace terms. |
| Enterprise add-ons | RapidKit Commercial License | Direct contract                                           | Managed via enterprise agreements; entitlements map to contract SKUs.            |

______________________________________________________________________

## 2. License File Structure

The license file (`license.json`) is placed at the project root:

```json
{
    "license_id": "...",
    "issued_to": "...",
    "issued_at": "2025-08-24T00:00:00Z",
    "expires_at": null,
  "modules": ["billing"],
  "features": ["usage_metrics"],
  "channel": "marketplace",
  "support_plan": "priority",
    "signature": "..."
}
```

- `modules`: Premium modules that can be installed.
- `features`: Optional feature switches consumed by module code.
- `channel`: Optional indicator (`community`, `marketplace`, `contract`) describing how the license
  was issued. Marketplace automation sets this to `marketplace`.
- `support_plan`: Optional flag for attaching priority/enterprise support.

______________________________________________________________________

## 3. License CLI Usage

### Inspect License

```sh
rapidkit license inspect
```

Shows the current license information.

### Activate License

```sh
rapidkit license activate <license_file.json>
```

Activates a new license from a file.

______________________________________________________________________

## 4. Module Gating Enforcement

- When installing a module (`rapidkit add module <name>`), the CLI checks the module's
  `entitlements.modules` entries against the active license.
- If the entitlement is missing or expired, installation fails with a clear error message.
- Feature flags (`entitlements.features`) are passed into the module runtime to toggle behaviour.
- Support-plan checks happen separately when invoking `rapidkit support` commands.

______________________________________________________________________

## 5. Developer Workflow

- Always set `entitlements.modules` in new module manifests for marketplace or enterprise modules.
- Use `rapidkit license inspect` to check the current license.
- Use `rapidkit license activate` to update the license.
- Attempting to add a gated module without the required entitlement results in a clear error.

______________________________________________________________________

## 6. Extending/Customizing

- To introduce new entitlements, update the manifest schema and CLI validation logic. Marketplace
  onboarding must assign entitlement IDs before publication.
- For per-feature gating, extend `entitlements.features` and validate inside the module's
  `pre_install` hook.

______________________________________________________________________

## 8. Alignment with Kits

- Each framework bundles a single **standard kit** that ships under an open-source license and does
  not require a commercial entitlement.
- Premium kits (when available) follow the same entitlement model as marketplace modules and are
  distributed under the RapidKit Commercial License.
- Kit metadata stored in `licenses/kits/*.json` should mirror the module rules above, including the
  `channel` field when the kit is sold via the marketplace.

______________________________________________________________________

## 9. Security & Audit

- All license activations and module installations are auditable via CLI logs.
- License signatures can be verified for authenticity (future extension).

______________________________________________________________________

## 10. Support

For questions or issues, contact the RapidKit core team.
