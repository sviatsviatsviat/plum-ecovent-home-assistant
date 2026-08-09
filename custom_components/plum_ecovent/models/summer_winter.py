"""Resolve and validate summer / winter mode (REKWS2) and related setpoints."""

from __future__ import annotations

from typing import Any

from ..const import (
    PARAM_SUMMER_HYSTERESIS,
    PARAM_SUMMER_HYSTERESIS_ID,
    PARAM_SUMMER_WINTER_MODE,
    PARAM_SUMMER_WINTER_MODE_ID,
    PARAM_WINTER_ACTIVE_TEMP,
    PARAM_WINTER_ACTIVE_TEMP_ID,
)
from ..parameters import (
    OPTION_UNSUPPORTED,
    EditableNumberStatus,
    EditParamIndex,
    MappedParamStatus,
    WireMappedIntEnum,
    resolve_writable_data_number,
    resolve_writable_data_param,
)

__all__ = [
    "OPTION_UNSUPPORTED",
    "SUMMER_HYSTERESIS_MAX",
    "SUMMER_HYSTERESIS_MIN",
    "SUMMER_WINTER_MODES",
    "SummerWinterMode",
    "SummerWinterModeStatus",
    "WINTER_ACTIVE_TEMP_MAX",
    "WINTER_ACTIVE_TEMP_MIN",
    "resolve_summer_hysteresis",
    "resolve_summer_winter_mode",
    "resolve_winter_active_temp",
]

SummerWinterModeStatus = MappedParamStatus

# Documented module ranges (§3.6 Related summer / winter parameters).
WINTER_ACTIVE_TEMP_MIN = -20.0
WINTER_ACTIVE_TEMP_MAX = 20.0
SUMMER_HYSTERESIS_MIN = 0.0
SUMMER_HYSTERESIS_MAX = 20.0


class SummerWinterMode(WireMappedIntEnum):
    """Writable REKWS2 wire values (Summer / Winter / Auto / Ventilation)."""

    SUMMER = 1
    WINTER = 2
    AUTO = 5
    VENTILATION = 8


# Select option order matches the ecoVENT UI listing.
SUMMER_WINTER_MODES: tuple[SummerWinterMode, ...] = (
    SummerWinterMode.SUMMER,
    SummerWinterMode.WINTER,
    SummerWinterMode.AUTO,
    SummerWinterMode.VENTILATION,
)


def resolve_summer_winter_mode(
    edit_params: dict[str, Any],
    reg_params: dict[str, Any] | None = None,
    data_index: EditParamIndex | None = None,
) -> SummerWinterModeStatus:
    """Validate REKWS2 id/edit and return the wire from editParams.data."""
    return resolve_writable_data_param(
        edit_params,
        name=PARAM_SUMMER_WINTER_MODE,
        expected_id=PARAM_SUMMER_WINTER_MODE_ID,
        mode_cls=SummerWinterMode,
        reg_params=reg_params,
        data_index=data_index,
    )


def resolve_winter_active_temp(
    edit_params: dict[str, Any],
    reg_params: dict[str, Any] | None = None,
    data_index: EditParamIndex | None = None,
) -> EditableNumberStatus:
    """Validate REKwinterActiveTemp identity and return value/min/max."""
    return resolve_writable_data_number(
        edit_params,
        name=PARAM_WINTER_ACTIVE_TEMP,
        expected_id=PARAM_WINTER_ACTIVE_TEMP_ID,
        reg_params=reg_params,
        fallback_min=WINTER_ACTIVE_TEMP_MIN,
        fallback_max=WINTER_ACTIVE_TEMP_MAX,
        data_index=data_index,
    )


def resolve_summer_hysteresis(
    edit_params: dict[str, Any],
    reg_params: dict[str, Any] | None = None,
    data_index: EditParamIndex | None = None,
) -> EditableNumberStatus:
    """Validate REKsummerHyst identity and return value/min/max."""
    return resolve_writable_data_number(
        edit_params,
        name=PARAM_SUMMER_HYSTERESIS,
        expected_id=PARAM_SUMMER_HYSTERESIS_ID,
        reg_params=reg_params,
        fallback_min=SUMMER_HYSTERESIS_MIN,
        fallback_max=SUMMER_HYSTERESIS_MAX,
        data_index=data_index,
    )
