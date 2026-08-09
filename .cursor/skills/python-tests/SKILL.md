---
name: python-tests
description: Test Plum ecoVENT config flow, setup, platforms, and entities with pytest-homeassistant-custom-component. Use when adding tests, reviewing test quality, or implementing integration behavior.
---

# Python tests

Follow [AGENTS.md](../../../AGENTS.md) and the current patterns under `tests/`.

## Layers

| Layer | Location | Rule |
|---|---|---|
| Unit / integration | `tests/` | Use HA test harness; assert config entries, states, and services. Mock device I/O at boundaries. |
| Manual HA run | `config/` via debug/task | Smoke-check UI and live reload; not a substitute for pytest. |

## General rules

- Assert observable Home Assistant behavior; no placeholder or tautological tests.
- Keep the autouse `enable_custom_integrations` fixture in `tests/conftest.py`.
- Prefer `MockConfigEntry` and full `async_setup` / unload paths for entity tests.
- Use focused patches for collaborators; avoid over-mocking HA internals.
- When network/device clients exist, inject or patch them — never call real ecoNET hardware from CI/unit tests.
- Name tests after the behavior under test (`test_setup_entry_forwards_sensor_platform`).

## Config flow and setup

Cover as applicable:

- successful create/abort paths;
- `single_config_entry` rejection of a second entry;
- `async_setup_entry` platform forwarding;
- entity unique IDs, states, and attributes;
- clean unload / reload behavior.

## Verification

```bash
/home/vscode/.venv/bin/python -m pytest
/home/vscode/.venv/bin/python -m pytest tests/test_init.py -q
/home/vscode/.venv/bin/python -m ruff check .
```
