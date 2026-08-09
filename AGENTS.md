# Repository instructions

`plum-ecovent-home-assistant` is a Home Assistant custom integration for Plum ecoVENT (`custom_components/plum_ecovent`). Development targets a disposable HA instance under `config/` inside the Dev Container.

Read these committed references before changing behavior:

- [README](README.md) for HACS install, configuration, and shipped entities.
- [Contributing](CONTRIBUTING.md) for Dev Container setup, run/test/lint, docs, changelog, commits, and CI.
- [Changelog](CHANGELOG.md) for user-visible release notes.
- [Architecture](docs/architecture.md) for package responsibilities, data flow, and extension boundaries.
- [manifest.json](custom_components/plum_ecovent/manifest.json) for domain, config flow, `single_config_entry`, version, and IoT class.
- [AGENTS.md](AGENTS.md) (this file) for non-negotiable agent workflow.
- Cursor rules under `.cursor/rules/` and skills under `.cursor/skills/`.

## Package map

- `custom_components/plum_ecovent/`: the integration (domain `plum_ecovent`).
  - `coordinator/`: polling, runtime identity validation, and atomic snapshots.
  - `models/`: ecoNET-specific modes, presets, and validated device statuses.
  - `parameters/`: reusable payload parsing and name/id validation.
  - `sensor/`, `select/`, `number/`: Home Assistant platform presentation.
- `docs/architecture.md`: dependency direction, data/write flows, invariants, and guidance for placing new behavior.
- `tests/`: pytest suite using `pytest-homeassistant-custom-component`.
- `config/`: disposable Home Assistant config used by the debugger/tasks. `config/custom_components` is a symlink to `../custom_components` (created by the Dev Container post-create command).
- `.devcontainer/`: Python 3.14 Dev Container; venv at `/home/vscode/.venv`. Do not create a project-root `.venv` for day-to-day work unless asked.
- `.vscode/`: launch, tasks, and interpreter settings for that venv.
- `requirements-dev.txt`: pinned Home Assistant, pytest helper, ruff, debugpy.
- `pyproject.toml`: pytest and ruff configuration.
- `hacs.json`: HACS metadata.

## Non-negotiable boundaries

- Integration code lives only under `custom_components/plum_ecovent/`. Do not copy it into `config/`; rely on the symlink.
- Do not modify a production Home Assistant install; use `config/` only.
- Prefer async Home Assistant patterns (`async_setup_entry`, platforms, config flow) consistent with current HA APIs.
- Pin dependency versions in `requirements-dev.txt`. When bumping one pin, update every reference to that dependency in the same change. Keep pins synchronized with CONTRIBUTING/AGENTS verification commands; audit workflow `uses:` pins with [`.cursor/skills/ci-pins/SKILL.md`](.cursor/skills/ci-pins/SKILL.md).
- Use conventional commits with imperative subjects: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, or `chore:`.
- Do not call real ecoNET hardware from unit tests; mock at the API boundary.
- Preserve attribution for the adapted bulgur/plum-econet client (`NOTICE`, `api.py` header, README Acknowledgments).

## Required verification

```bash
/home/vscode/.venv/bin/python -m pytest
/home/vscode/.venv/bin/python -m ruff check .
```

Use focused pytest selection while iterating, then run the full suite. New user-visible integration behavior needs tests in the same change. The Linux Dev Container is the authoritative local environment; GitHub Actions CI must stay green on `main` / PRs.

## Change hygiene

- User-visible integration, entity, config-flow, or security behavior belongs in `CHANGELOG.md`. Internal refactors, CI, tests, docs-only edits, and agent tooling do not. Follow [Contributing](CONTRIBUTING.md#changelog-policy).
- Update README together when described setup or behavior changes.
- Keep GitHub Actions and tool versions exactly pinned when workflows exist (`@vN.N.N` by default; see [ci-pins](.cursor/skills/ci-pins/SKILL.md) for the `hacs/action` and hassfest SHA exceptions).
- Pull request summaries cover the full branch and list verification.
