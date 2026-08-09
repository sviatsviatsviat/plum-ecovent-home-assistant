"""Diagnostics support for Plum ecoVENT."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import PlumEconetConfigEntry
from .models.wifi import wifi_diagnostics_snapshot

TO_REDACT = {
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    "password",
    "login",
    "key",
    "ssid",
    "wlan0",
    "servicePassword",
    "etPasswords",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PlumEconetConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    curr = coordinator.reg_params.get("curr")
    curr_keys = sorted(curr) if isinstance(curr, dict) else []
    data = coordinator.edit_params.get("data")
    data_count = len(data) if isinstance(data, dict) else 0
    return {
        "entry": async_redact_data(
            {
                "title": entry.title,
                "unique_id": entry.unique_id,
                "data": dict(entry.data),
            },
            TO_REDACT,
        ),
        "wifi": async_redact_data(
            wifi_diagnostics_snapshot(coordinator.sys_params), TO_REDACT
        ),
        "sys_params": async_redact_data(coordinator.sys_params, TO_REDACT),
        "reg_params": {
            "settingsVer": coordinator.reg_params.get("settingsVer"),
            "editableParamsVer": coordinator.reg_params.get("editableParamsVer"),
            "curr_keys": curr_keys,
        },
        "edit_params": {
            "editableParamsVer": coordinator.edit_params.get("editableParamsVer"),
            "data_count": data_count,
        },
    }
