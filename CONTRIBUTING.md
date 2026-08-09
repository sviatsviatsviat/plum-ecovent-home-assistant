# Contributing to Plum ecoVENT

Changes are expected to keep code, tests, user documentation, and the changelog aligned. Start with [README](README.md) for shipped entities and end-user setup, then use this guide for the development workflow. Agents should also follow [AGENTS.md](AGENTS.md).

## Development environment

The project requires Python **3.14.2+** (see `pyproject.toml`).

Use the pinned Linux [Dev Container](.devcontainer/) for the authoritative verification suite.

1. Install Docker, Visual Studio Code, and the **Dev Containers** extension.
2. Open this repository in Visual Studio Code.
3. Run **Dev Containers: Reopen in Container** from the Command Palette.
4. Wait for the post-create setup to install the pinned dependencies.

After creating the container, dependencies install into `/home/vscode/.venv`, and `config/custom_components` is symlinked to the repo `custom_components/` tree. Home Assistant therefore loads edits directly; there is no copy step. The Python virtual environment lives on the container's native Linux filesystem, avoiding slow virtualenv I/O on Windows bind mounts.

A local venv is fine for editing and focused tests, but keep pins identical to `requirements-dev.txt`.

Before submitting a change:

```bash
/home/vscode/.venv/bin/python -m pytest
/home/vscode/.venv/bin/python -m ruff check .
```

GitHub Actions (`.github/workflows/ci.yml`) runs Python lint/tests on every push and pull request to `main`. Validation (`.github/workflows/validate.yml`) runs hassfest and the HACS Action on the same events plus a daily schedule. Dependabot (`.github/dependabot.yml`) opens weekly PRs for GitHub Actions, pip pins, Dev Container features, and the Dev Container base image. Pip updates for `homeassistant` and `pytest-homeassistant-custom-component` are grouped so they stay compatible; bump `hacs.json` `homeassistant` and the README minimum in the same change.

Do not point development at a production Home Assistant install.

## Run Home Assistant

Run the **Home Assistant: Run** task with **Terminal: Run Task**, or run:

```bash
/home/vscode/.venv/bin/python -m homeassistant -c config
```

Open [http://localhost:8123](http://localhost:8123), complete Home Assistant's first-run onboarding, then:

1. Go to **Settings → Devices & services**.
2. Select **Add integration**.
3. Search for **Plum ecoVENT**.
4. Enter the module host/IP, username, and password, and enable **Allow insecure HTTP** (required for the module’s cleartext LAN API).

The integration permits only one config entry. Remove any previous stub entry before adding a live module.

All generated Home Assistant state is stored in `config/` and ignored by Git. This setup does not use or modify a production Home Assistant installation.

## Test and lint

Use the **Tests** and **Lint** VS Code tasks, or run inside the container:

```bash
/home/vscode/.venv/bin/python -m pytest
/home/vscode/.venv/bin/python -m ruff check .
```

To debug Home Assistant, open **Run and Debug**, select **Home Assistant**, and start it. Breakpoints in `custom_components/plum_ecovent` are loaded directly.

## Find the right place

| Change | Primary location |
|---|---|
| Integration setup / unload | `custom_components/plum_ecovent/__init__.py` |
| Config flow | `custom_components/plum_ecovent/config_flow.py` |
| Polling / snapshot assembly | `custom_components/plum_ecovent/coordinator/` |
| Device modes and statuses | `custom_components/plum_ecovent/models/` |
| Parameter parsing / validation | `custom_components/plum_ecovent/parameters/` |
| Platforms (e.g. sensor) | `custom_components/plum_ecovent/<platform>/` |
| Constants / domain | `custom_components/plum_ecovent/const.py` |
| Manifest / HACS metadata | `manifest.json`, `hacs.json` |
| Strings / translations | `translations/` (do not use `strings.json`) |
| Tests | `tests/` |
| Dev Container / editor | `.devcontainer/`, `.vscode/` |
| Pins and tool config | `requirements-dev.txt`, `pyproject.toml` |

Integration code lives only under `custom_components/plum_ecovent/`. Do not copy sources into `config/`; rely on the symlink created by the Dev Container.

## Implementing changes

### User-visible integration changes

- Prefer current Home Assistant async patterns (`async_setup_entry`, platforms, config flow helpers).
- Keep milestone scope honest: do not add ecoNET network I/O, discovery, authentication, coordinators, or real recuperator entities unless the task explicitly expands scope.
- Add or update pytest coverage for config flow, setup, entity state, and unload/reload as applicable.
- Update [README](README.md) and [CHANGELOG.md](CHANGELOG.md) in the same change when users can observe the behavior.

### Internal changes

Internal refactors still need tests when behavior or invariants can regress. They do not need a changelog entry unless users observe a change.

### Tooling and environment changes

Keep Dev Container, VS Code tasks/launch settings, and this guide's commands consistent with the venv path and verification commands. Pin exact package versions in `requirements-dev.txt`.

## Tests

Tests must assert Home Assistant behavior rather than implementation bookkeeping.

| Layer | Location | Scope |
|---|---|---|
| Automated | `tests/` | `pytest-homeassistant-custom-component`; config entries, states, flow results; mock device I/O at boundaries |
| Manual | `config/` via task/debugger | UI onboarding and live reload smoke checks |

- Keep the autouse `enable_custom_integrations` fixture in `tests/conftest.py`.
- Prefer `MockConfigEntry` and full setup/unload paths for entity tests.
- Never call real ecoNET hardware from unit tests.
- Name tests after the behavior under test.

Run a focused pytest selection while iterating, then the complete verification suite before handoff.

## Documentation

User-facing behavior has two primary documentation layers:

1. [README](README.md) for HACS/manual install, configuration, and entities;
2. [CHANGELOG.md](CHANGELOG.md) for release-level outcomes.

Development setup, verification, and contribution policy live in this guide. Update affected layers in the same pull request. Avoid documenting planned entities, services, or device APIs as if they already ship.

The implementation architecture, dependency direction, read/write flows, and extension boundaries are documented in [docs/architecture.md](docs/architecture.md). Keep that guide aligned when a change moves responsibilities between packages or introduces a new layer.

Module and function docstrings should be short complete sentences that describe behavior. Follow existing style in `custom_components/plum_ecovent/`.

## Changelog policy

The changelog is for behavior available to Home Assistant users:

- config flow steps, options, and abort reasons;
- entities, devices, services, and attributes;
- setup/unload/reload behavior that affects the UI or automations;
- security fixes.

Do not add entries for repository scaffolding, CI, lint configuration, tests, agent instructions, documentation-only edits, or internal refactors with no visible effect. Entries should describe what a user can do and the behavior they can rely on.

Use Keep a Changelog sections. Until there is a published baseline beyond the initial stub, describe new shipped behavior under `Added`; use `Changed` or `Removed` only relative to behavior users could obtain from a tagged release.

## Version pinning

Python package pins in `requirements-dev.txt`, Dev Container feature versions (for example GitHub CLI in `.devcontainer/devcontainer.json`), and GitHub Action versions are exact. Never introduce `@latest`, branch tags, or floating major/minor Action tags.

Allowed workflow `uses:` pins:

- Exact `@vN.N.N` release tags (default).
- `hacs/action@N.N.N` only (HACS tags omit the `v` prefix).
- `home-assistant/actions/hassfest@` plus a full 40-character commit SHA only.

When bumping a dependency, update every reference to that same dependency in the same pull request (requirements, workflows, `hacs.json` `homeassistant` when the Home Assistant pin changes, and docs that cite the version).

Audit every workflow `uses:` pin with the command in [`.cursor/skills/ci-pins/SKILL.md`](.cursor/skills/ci-pins/SKILL.md). It must exit 0 with no violations.

## Cutting a release

Releases are git tags. HACS installs from GitHub Releases (not PyPI). Keep `custom_components/plum_ecovent/manifest.json` `version` and `pyproject.toml` `[project].version` aligned with the release as `X.Y.Z` (no `v`). Git tags use the `v` prefix (`vX.Y.Z`); changelog headings omit it (`## [X.Y.Z]`).

1. On `main`, promote `## [Unreleased]` in `CHANGELOG.md` to `## [X.Y.Z] - YYYY-MM-DD` (or a pre-release such as `0.1.0-alpha`), leave a fresh empty `## [Unreleased]`, set `manifest.json` and `pyproject.toml` versions to `X.Y.Z`, and merge after CI and validate are green. The heading version must match the tag without the leading `v`.
2. Create and push only the annotated tag on that `main` commit (`git tag -a vX.Y.Z && git push origin vX.Y.Z`). The release workflow refuses tags whose commit is not an ancestor of `origin/main`. Do not craft the Release body by hand; `.github/workflows/release.yml` fills notes from that changelog section via `.github/scripts/changelog-section.sh` (strips the tag’s leading `v` when looking up the heading).
3. Confirm the GitHub Release page. Pre-release tags (`vX.Y.Z-…`) are marked as GitHub prereleases.

## Commits and pull requests

Use an imperative conventional commit subject:

```text
feat(config_flow): reject a second Plum ecoVENT entry
fix(sensor): restore stub status after reload
docs: explain config/custom_components symlink
```

Supported prefixes are `feat`, `fix`, `refactor`, `test`, `docs`, and `chore`. Use the body to explain why the change is needed when the subject is not enough.

A pull request should:

- summarize the full branch, not only the last commit;
- call out user-visible behavior and compatibility;
- list verification performed;
- include documentation and changelog updates when required;
- keep unrelated cleanup out of the change.
