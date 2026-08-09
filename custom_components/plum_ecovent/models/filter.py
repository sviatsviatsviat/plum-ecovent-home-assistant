"""Validate fixed filter informationParams slots against FILTERtimeToAlarm."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..const import (
    INFO_SLOT_EXTRACT_FILTER_DAYS,
    INFO_SLOT_EXTRACT_FILTER_DEPLETION,
    INFO_SLOT_SUPPLY_FILTER_DAYS,
    INFO_SLOT_SUPPLY_FILTER_DEPLETION,
    INFO_UNIT_DAYS,
    INFO_UNIT_PERCENT,
    PARAM_FILTER_TIME_TO_ALARM,
)
from ..parameters import EditParamIndex, find_data_entry_by_name

# Absolute percent-point tolerance for depletion ≈ days / timeToAlarm × 100.
_DEPL_ABS_TOL = 0.05

# FilterStatus field names (coordinator.filter_status / sensor value_attr).
ATTR_SUPPLY_DEPLETION = "supply_depletion"
ATTR_EXTRACT_DEPLETION = "extract_depletion"
ATTR_SUPPLY_DAYS = "supply_days"
ATTR_EXTRACT_DAYS = "extract_days"
ATTR_SUPPLY_DAYS_TO_ALERT = "supply_days_to_alert"
ATTR_EXTRACT_DAYS_TO_ALERT = "extract_days_to_alert"

# PlumEconetCoordinator attribute holding FilterStatus.
COORDINATOR_ATTR_FILTER_STATUS = "filter_status"


@dataclass(frozen=True, slots=True)
class FilterStatus:
    """Validated filter depletion, operation days, and days remaining to alert."""

    supply_depletion: float | None
    extract_depletion: float | None
    supply_days: float | None
    extract_days: float | None
    supply_days_to_alert: float | None
    extract_days_to_alert: float | None


def _filter_time_to_alarm(
    edit_params: dict[str, Any],
    data_index: EditParamIndex | None = None,
) -> float | None:
    """Return FILTERtimeToAlarm value from data, keyed by name (not id)."""
    resolved = find_data_entry_by_name(
        edit_params, PARAM_FILTER_TIME_TO_ALARM, data_index
    )
    if resolved is None:
        return None
    _, entry = resolved
    try:
        value = float(entry.get("value"))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return value


def _parse_info_slot(entry: Any) -> tuple[float, int] | None:
    """Parse [visible, [[value, unit, …]]] into (value, unit)."""
    if not isinstance(entry, list) or len(entry) < 2:
        return None
    values = entry[1]
    if not isinstance(values, list) or not values:
        return None
    row = values[0]
    if not isinstance(row, list) or len(row) < 2:
        return None
    try:
        value = float(row[0])
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    unit = row[1]
    # Reject bool (subclass of int) and non-int units such as 2.5.
    if isinstance(unit, bool) or not isinstance(unit, int):
        return None
    return value, unit


def _slot_value(
    information_params: dict[str, Any],
    slot_id: str,
    expected_unit: int,
) -> float | None:
    """Return a slot value when it exists with the expected presentation unit."""
    parsed = _parse_info_slot(information_params.get(slot_id))
    if parsed is None:
        return None
    value, unit = parsed
    if unit != expected_unit:
        return None
    return value


def _matches_time_to_alarm(days: float, time_to_alarm: float, pct: float) -> bool:
    """Return True when pct ≈ days / timeToAlarm × 100."""
    expected = days / time_to_alarm * 100.0
    return abs(pct - expected) <= _DEPL_ABS_TOL


def _days_to_alert(days: float | None, time_to_alarm: float | None) -> float | None:
    """Return days remaining until the alert threshold (floored at 0)."""
    if days is None or time_to_alarm is None:
        return None
    return max(0.0, time_to_alarm - days)


def _validated_pair(
    *,
    depletion: float | None,
    days: float | None,
    time_to_alarm: float | None,
) -> tuple[float | None, float | None]:
    """Return (depletion, days) when both match FILTERtimeToAlarm; else Nones."""
    if (
        time_to_alarm is None
        or depletion is None
        or days is None
        or not _matches_time_to_alarm(days, time_to_alarm, depletion)
    ):
        return None, None
    return depletion, days


def resolve_filter_status(
    edit_params: dict[str, Any],
    data_index: EditParamIndex | None = None,
) -> FilterStatus:
    """Read fixed slots 61–64 and validate each side against FILTERtimeToAlarm."""
    time_to_alarm = _filter_time_to_alarm(edit_params, data_index)
    empty = FilterStatus(
        supply_depletion=None,
        extract_depletion=None,
        supply_days=None,
        extract_days=None,
        supply_days_to_alert=None,
        extract_days_to_alert=None,
    )
    information_params = edit_params.get("informationParams")
    if not isinstance(information_params, dict):
        return empty

    supply_depletion, supply_days = _validated_pair(
        depletion=_slot_value(
            information_params,
            INFO_SLOT_SUPPLY_FILTER_DEPLETION,
            INFO_UNIT_PERCENT,
        ),
        days=_slot_value(
            information_params,
            INFO_SLOT_SUPPLY_FILTER_DAYS,
            INFO_UNIT_DAYS,
        ),
        time_to_alarm=time_to_alarm,
    )
    extract_depletion, extract_days = _validated_pair(
        depletion=_slot_value(
            information_params,
            INFO_SLOT_EXTRACT_FILTER_DEPLETION,
            INFO_UNIT_PERCENT,
        ),
        days=_slot_value(
            information_params,
            INFO_SLOT_EXTRACT_FILTER_DAYS,
            INFO_UNIT_DAYS,
        ),
        time_to_alarm=time_to_alarm,
    )
    return FilterStatus(
        supply_depletion=supply_depletion,
        extract_depletion=extract_depletion,
        supply_days=supply_days,
        extract_days=extract_days,
        supply_days_to_alert=_days_to_alert(supply_days, time_to_alarm),
        extract_days_to_alert=_days_to_alert(extract_days, time_to_alarm),
    )
