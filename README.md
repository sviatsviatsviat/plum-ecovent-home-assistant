![Plum ecoVENT](custom_components/plum_ecovent/brand/logo.png)

# Plum ecoVENT for Home Assistant

Local Home Assistant custom integration for Plum ecoVENT recuperators with an ecoNET300 module. Add the module host/IP and local credentials once; the integration talks to the module over your LAN using HTTP Basic auth.

> **This is not an official Plum or Home Assistant integration.** It is an independent project and is not affiliated with, endorsed by, or supported by Plum Sp. z o.o. or the Home Assistant project.

## Installation

Requires Home Assistant **2026.8.0** or newer (enforced by HACS).

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sviatsviatsviat&repository=plum-ecovent-home-assistant&category=integration)

1. Install [HACS](https://hacs.xyz/) if it is not already installed.
2. In Home Assistant, open **HACS**.
3. Use the badge above, or add this repository as a custom repository:
   - Menu (⋮) → **Custom repositories**
   - Repository: `https://github.com/sviatsviatsviat/plum-ecovent-home-assistant`
   - Category: **Integration**
4. Find **Plum ecoVENT**, select **Download**, then restart Home Assistant.

### Manual

1. Copy `custom_components/plum_ecovent` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & services**.
2. Select **Add integration** and search for **Plum ecoVENT**.
3. Enter the module host/IP, username, and password.
4. Enable **Allow insecure HTTP**. Enable it only on a local trusted network or another trusted network (for example over a VPN).

Only one Plum ecoVENT config entry is allowed. If the module credentials change, Home Assistant starts a reauthentication flow that updates the existing entry after confirming it is the same module.

> **Security note:** The ecoNET300 module uses HTTP Basic auth over cleartext HTTP, so credentials are not encrypted on the wire. **Allow insecure HTTP** is required and shows a warning when enabled—use it only on a trusted LAN or VPN. Without that opt-in, the integration refuses cleartext HTTP and rejects redirects to `http://` destinations.

## Entities

### Controls

- Recuperation operation mode — Halt, Mode 1–4
- Additional work mode — Off, Outside, Party, Airing

Unexpected mode values appear as read-only Unsupported.

### Sensors

- Supply and exhaust fan speed (%)
- Supply, intake, extracted, and exhaust air temperature (°C)
- Supply and extracted air filter depletion (%)
- Supply and extracted air filter operation days
- Party / Outside / Airing remaining time (minutes); `0` when that mode is idle
- Bypass / Rotor motor state (Off / On) and bypass open level (%)

### Configuration

- Summer / winter mode — Summer, Winter, Auto, Ventilation
- Bypass mode — Auto, Open, Close
- Summer mode hysteresis (°C) and Winter mode turn-on temperature (°C)
- Party supply/exhaust fan speed (%), duration (hours), and target temperature (°C); Outside duration (hours); Airing exhaust fan speed (%) and duration (minutes)
- Mode 1–4 supply and exhaust fan velocities (%)
- Mode 1–4 target temperatures (°C)

### Diagnostic

- Supply and extracted air filter days to alert
- Comfort, leading, and external temperatures (°C)
- Control mode (Heating / Cooling)
- Summer / Winter status
- Wi‑Fi signal (dBm) and link quality (%), disabled by default

## Acknowledgments

The LAN HTTP client is adapted from [bulgur/plum-econet](https://gitlab.com/bulgur/plum-econet) by Paweł Tomak (MIT License). See [NOTICE](NOTICE) for the full attribution.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, [CHANGELOG.md](CHANGELOG.md) for user-visible release notes, [docs/architecture.md](docs/architecture.md) for package boundaries, and [docs/econet-local-api.md](docs/econet-local-api.md) for local ecoNET300 HTTP API research notes.
