---
name: changelog
description: Maintain CHANGELOG.md as a concise record of user-visible integration, entity, config-flow, and security behavior. Use when adding release notes, documenting shipped user-facing features, or editing the [Unreleased] section.
---

# Changelog

Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the policy in [CONTRIBUTING.md](../../../CONTRIBUTING.md#changelog-policy). Prefer the condensed style of the current [CHANGELOG.md](../../../CHANGELOG.md): short outcome bullets grouped by setup, entities, and security—not protocol or attribute dumps.

## Include

Add an entry when users can observe a new or changed:

- config flow step, option, or abort reason;
- entity, device, service, or attribute;
- setup/unload/reload behavior that affects the UI or automations;
- security property (credentials handling, local-only guarantees).

Write outcomes, not implementation history:

```markdown
- Config flow rejects a second Plum ecoVENT entry.
```

Do not name wire params, HTTP paths, MDI icons, or internal attributes (`pending_write`, `assumed_state`, etc.).

## Exclude

Do not mention scaffolding of repository packages, internal refactors, test harnesses, CI/lint changes, agent rules/skills, or documentation-only work.

Keep related details under one feature bullet.

## Sections

Use `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security`.

Before a published baseline, put shipped behavior under `Added` only. Do not use `Fixed`, `Changed`, or `Removed` until users could obtain the prior behavior from a tagged release.

If a change has no user-visible behavior, leave the changelog untouched.
