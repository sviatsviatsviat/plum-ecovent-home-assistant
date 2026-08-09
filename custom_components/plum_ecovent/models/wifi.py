"""Wi-Fi link fields from ecoNET sysParams."""

from __future__ import annotations

from typing import Any

from ..parameters.numeric import parse_finite_number

SYS_PARAM_WIFI = "wifi"
SYS_PARAM_SIGNAL = "signal"
SYS_PARAM_QUALITY = "quality"


def parse_sys_param_number(value: Any) -> float | None:
    """Return a finite float from a sysParams field, or None if invalid."""
    return parse_finite_number(value)


def wifi_diagnostics_snapshot(sys_params: dict[str, Any]) -> dict[str, Any]:
    """Stable Wi-Fi fields for config-entry diagnostics (no secrets)."""
    snapshot: dict[str, Any] = {}
    if SYS_PARAM_WIFI in sys_params:
        snapshot["wifi"] = sys_params[SYS_PARAM_WIFI]
    if SYS_PARAM_SIGNAL in sys_params:
        snapshot["signal"] = parse_sys_param_number(sys_params[SYS_PARAM_SIGNAL])
    if SYS_PARAM_QUALITY in sys_params:
        snapshot["quality"] = parse_sys_param_number(sys_params[SYS_PARAM_QUALITY])
    return snapshot
