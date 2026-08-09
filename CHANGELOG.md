# Changelog

All notable user-visible changes to the Plum ecoVENT Home Assistant integration are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project intends to use [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-08-09

### Added

- Requires Home Assistant 2026.8.0 or newer (enforced via HACS).
- **Plum ecoVENT** integration (`plum_ecovent`) for a single local ecoNET300 module (host/IP, username, password, **Allow insecure HTTP**).
- Reauthentication when local credentials change; the new credentials must belong to the same module before the entry is updated.
- Device registry entry for the module (manufacturer Plum) with polled live state.
- Config-entry diagnostics with sensitive fields redacted.
- Controls: recuperation operation mode (Halt, Mode 1–4) and additional work mode (Off, Outside, Party, Airing). Unexpected mode values appear as read-only Unsupported.
- Sensors: supply/exhaust fan speed; supply, intake, extracted, and exhaust air temperatures; filter depletion and operation days; Party/Outside/Airing remaining time; bypass/rotor motor state and bypass open level.
- Configuration: summer/winter mode and setpoints; bypass mode; Party/Outside/Airing presets; Mode 1–4 fan velocities and target temperatures.
- Diagnostic: filter days to alert; comfort, leading, and external temperatures; control mode; summer/winter status; Wi‑Fi signal and link quality (disabled by default).
- After a successful write, selects and numbers keep the UI value for up to 30 seconds until the module confirms it.
- Polling keeps the last good snapshot if an endpoint fails, and refuses to follow a different module UID at the configured host.
- Malformed HTTP success responses are treated as connection failures in setup and polling.

### Security

- Credentials are stored in config-entry data and omitted from logs and unredacted diagnostics. Use only on a trusted LAN or VPN.
- Cleartext HTTP requires **Allow insecure HTTP**; the config flow warns when it is enabled. API requests refuse cleartext HTTP without that opt-in and reject redirects to `http://` destinations.
