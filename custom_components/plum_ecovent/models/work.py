"""Resolve Current work status from editParams.informationParams slots 101–105."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..const import (
    INFO_SLOT_CONTROL_MODE,
    INFO_SLOT_CURRENT_COMFORT_TEMP,
    INFO_SLOT_CURRENT_LEADING_TEMP,
    INFO_SLOT_EXTERNAL_TEMP,
    INFO_SLOT_SUMMER_WINTER_STATUS,
    INFO_UNIT_CELSIUS,
    INFO_UNIT_MODE,
)
from ..parameters import OPTION_UNSUPPORTED, WireMappedIntEnum, parse_wire
from ..parameters.numeric import parse_finite_number

# WorkStatus field / property names (coordinator.work_status / sensor attrs).
ATTR_COMFORT_TEMPERATURE = "comfort_temperature"
ATTR_LEADING_TEMPERATURE = "leading_temperature"
ATTR_EXTERNAL_TEMPERATURE = "external_temperature"
ATTR_CONTROL_MODE_OPTION = "control_mode_option"
ATTR_SEASON_STATUS_OPTION = "season_status_option"

# PlumEconetCoordinator attribute holding WorkStatus.
COORDINATOR_ATTR_WORK_STATUS = "work_status"

__all__ = [
    "ATTR_COMFORT_TEMPERATURE",
    "ATTR_CONTROL_MODE_OPTION",
    "ATTR_EXTERNAL_TEMPERATURE",
    "ATTR_LEADING_TEMPERATURE",
    "ATTR_SEASON_STATUS_OPTION",
    "CONTROL_MODES",
    "COORDINATOR_ATTR_WORK_STATUS",
    "ControlMode",
    "OPTION_UNSUPPORTED",
    "SEASON_STATUSES",
    "SeasonStatus",
    "WorkStatus",
    "resolve_work_status",
]


class ControlMode(WireMappedIntEnum):
    """Wire values for informationParams slot 103 (Heating / Cooling)."""

    HEATING = 0
    COOLING = 1


class SeasonStatus(WireMappedIntEnum):
    """Wire values for informationParams slot 105 (Summer / Winter status)."""

    SUMMER = 0
    WINTER = 1
    AUTO_SUMMER = 2
    AUTO_WINTER = 3  # Documented assumption; not yet observed live.
    VENTILATION = 4


CONTROL_MODES: tuple[ControlMode, ...] = (
    ControlMode.HEATING,
    ControlMode.COOLING,
)

SEASON_STATUSES: tuple[SeasonStatus, ...] = (
    SeasonStatus.SUMMER,
    SeasonStatus.WINTER,
    SeasonStatus.AUTO_SUMMER,
    SeasonStatus.AUTO_WINTER,
    SeasonStatus.VENTILATION,
)


@dataclass(frozen=True, slots=True)
class WorkStatus:
    """Parsed Current work status panel values from informationParams."""

    comfort_temperature: float | None
    leading_temperature: float | None
    control_mode_wire: int | None
    external_temperature: float | None
    season_status_wire: int | None

    @property
    def control_mode_option(self) -> str | None:
        """Return Heating/Cooling option, Unsupported, or None if missing."""
        if self.control_mode_wire is None:
            return None
        mode = ControlMode.from_wire(self.control_mode_wire)
        return mode.option if mode is not None else OPTION_UNSUPPORTED

    @property
    def season_status_option(self) -> str | None:
        """Return season option, Unsupported, or None if missing."""
        if self.season_status_wire is None:
            return None
        mode = SeasonStatus.from_wire(self.season_status_wire)
        return mode.option if mode is not None else OPTION_UNSUPPORTED


def _parse_info_slot(entry: Any) -> tuple[Any, int] | None:
    """Parse [visible, [[value, unit, …]]] into (raw value, unit)."""
    if not isinstance(entry, list) or len(entry) < 2:
        return None
    values = entry[1]
    if not isinstance(values, list) or not values:
        return None
    row = values[0]
    if not isinstance(row, list) or len(row) < 2:
        return None
    unit = row[1]
    if isinstance(unit, bool) or not isinstance(unit, int):
        return None
    return row[0], unit


def _temperature_slot(
    information_params: dict[str, Any],
    slot_id: str,
) -> float | None:
    """Return a finite °C value when the slot uses presentation unit 1."""
    parsed = _parse_info_slot(information_params.get(slot_id))
    if parsed is None:
        return None
    raw, unit = parsed
    if unit != INFO_UNIT_CELSIUS:
        return None
    return parse_finite_number(raw)


def _mode_wire_slot(
    information_params: dict[str, Any],
    slot_id: str,
) -> int | None:
    """Return a wire int when the slot uses presentation unit 0."""
    parsed = _parse_info_slot(information_params.get(slot_id))
    if parsed is None:
        return None
    raw, unit = parsed
    if unit != INFO_UNIT_MODE:
        return None
    return parse_wire(raw)


def resolve_work_status(edit_params: dict[str, Any]) -> WorkStatus:
    """Read fixed slots 101–105 from informationParams (no writes)."""
    information_params = edit_params.get("informationParams")
    if not isinstance(information_params, dict):
        return WorkStatus(None, None, None, None, None)

    return WorkStatus(
        comfort_temperature=_temperature_slot(
            information_params, INFO_SLOT_CURRENT_COMFORT_TEMP
        ),
        leading_temperature=_temperature_slot(
            information_params, INFO_SLOT_CURRENT_LEADING_TEMP
        ),
        control_mode_wire=_mode_wire_slot(information_params, INFO_SLOT_CONTROL_MODE),
        external_temperature=_temperature_slot(
            information_params, INFO_SLOT_EXTERNAL_TEMP
        ),
        season_status_wire=_mode_wire_slot(
            information_params, INFO_SLOT_SUMMER_WINTER_STATUS
        ),
    )
