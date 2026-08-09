"""Additional / timed work mode duration, fan, and remaining-time parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime

from ..const import (
    PARAM_AIRING_DURATION,
    PARAM_AIRING_DURATION_ID,
    PARAM_AIRING_EXH_FAN_SPEED,
    PARAM_AIRING_EXH_FAN_SPEED_ID,
    PARAM_OUTSIDE_DURATION,
    PARAM_OUTSIDE_DURATION_ID,
    PARAM_PARTY_DURATION,
    PARAM_PARTY_DURATION_ID,
    PARAM_PARTY_EXH_FAN_SPEED,
    PARAM_PARTY_EXH_FAN_SPEED_ID,
    PARAM_PARTY_SETPOINT,
    PARAM_PARTY_SETPOINT_ID,
    PARAM_PARTY_SUP_FAN_SPEED,
    PARAM_PARTY_SUP_FAN_SPEED_ID,
    PARAM_TIME_TO_END_AIRING,
    PARAM_TIME_TO_END_AIRING_ID,
    PARAM_TIME_TO_END_OUTSIDE,
    PARAM_TIME_TO_END_OUTSIDE_ID,
    PARAM_TIME_TO_END_PARTY,
    PARAM_TIME_TO_END_PARTY_ID,
)
from ..parameters import (
    EditParamIndex,
    NumberParamStatus,
    resolve_readonly_number_param,
    resolve_writable_number_param,
)

# Documented module ranges (§3.5 Related Party/Outside/Airing parameters).
PRESET_FAN_MIN = 20.0
PRESET_FAN_MAX = 100.0
PRESET_SETPOINT_MIN = 8.0
PRESET_SETPOINT_MAX = 30.0
PARTY_OUTSIDE_DURATION_MIN = 0.0
PARTY_OUTSIDE_DURATION_MAX = 10.0
AIRING_DURATION_MIN = 0.0
AIRING_DURATION_MAX = 20.0


@dataclass(frozen=True, slots=True, kw_only=True)
class AdditionalWorkModeNumberSpec:
    """Static definition for one additional-mode number control."""

    key: str
    translation_key: str
    param_name: str
    param_id: int
    unit: str
    fallback_min: float
    fallback_max: float
    icon: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AdditionalWorkModeCountdownSpec:
    """Static definition for one remaining-time countdown sensor."""

    key: str
    translation_key: str
    param_name: str
    param_id: int


ADDITIONAL_WORK_MODE_NUMBERS: tuple[AdditionalWorkModeNumberSpec, ...] = (
    AdditionalWorkModeNumberSpec(
        key="party_supply_fan_speed",
        translation_key="party_supply_fan_speed",
        param_name=PARAM_PARTY_SUP_FAN_SPEED,
        param_id=PARAM_PARTY_SUP_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=PRESET_FAN_MIN,
        fallback_max=PRESET_FAN_MAX,
        icon="mdi:fan",
    ),
    AdditionalWorkModeNumberSpec(
        key="party_exhaust_fan_speed",
        translation_key="party_exhaust_fan_speed",
        param_name=PARAM_PARTY_EXH_FAN_SPEED,
        param_id=PARAM_PARTY_EXH_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=PRESET_FAN_MIN,
        fallback_max=PRESET_FAN_MAX,
        icon="mdi:fan",
    ),
    AdditionalWorkModeNumberSpec(
        key="party_duration",
        translation_key="party_duration",
        param_name=PARAM_PARTY_DURATION,
        param_id=PARAM_PARTY_DURATION_ID,
        unit=UnitOfTime.HOURS,
        fallback_min=PARTY_OUTSIDE_DURATION_MIN,
        fallback_max=PARTY_OUTSIDE_DURATION_MAX,
        icon="mdi:timer-outline",
    ),
    AdditionalWorkModeNumberSpec(
        key="party_preset_temperature",
        translation_key="party_preset_temperature",
        param_name=PARAM_PARTY_SETPOINT,
        param_id=PARAM_PARTY_SETPOINT_ID,
        unit=UnitOfTemperature.CELSIUS,
        fallback_min=PRESET_SETPOINT_MIN,
        fallback_max=PRESET_SETPOINT_MAX,
        icon="mdi:thermometer",
    ),
    AdditionalWorkModeNumberSpec(
        key="outside_duration",
        translation_key="outside_duration",
        param_name=PARAM_OUTSIDE_DURATION,
        param_id=PARAM_OUTSIDE_DURATION_ID,
        unit=UnitOfTime.HOURS,
        fallback_min=PARTY_OUTSIDE_DURATION_MIN,
        fallback_max=PARTY_OUTSIDE_DURATION_MAX,
        icon="mdi:timer-outline",
    ),
    AdditionalWorkModeNumberSpec(
        key="airing_exhaust_fan_speed",
        translation_key="airing_exhaust_fan_speed",
        param_name=PARAM_AIRING_EXH_FAN_SPEED,
        param_id=PARAM_AIRING_EXH_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=PRESET_FAN_MIN,
        fallback_max=PRESET_FAN_MAX,
        icon="mdi:fan",
    ),
    AdditionalWorkModeNumberSpec(
        key="airing_duration",
        translation_key="airing_duration",
        param_name=PARAM_AIRING_DURATION,
        param_id=PARAM_AIRING_DURATION_ID,
        unit=UnitOfTime.MINUTES,
        fallback_min=AIRING_DURATION_MIN,
        fallback_max=AIRING_DURATION_MAX,
        icon="mdi:timer-outline",
    ),
)

ADDITIONAL_WORK_MODE_COUNTDOWNS: tuple[AdditionalWorkModeCountdownSpec, ...] = (
    AdditionalWorkModeCountdownSpec(
        key="party_remaining_time",
        translation_key="party_remaining_time",
        param_name=PARAM_TIME_TO_END_PARTY,
        param_id=PARAM_TIME_TO_END_PARTY_ID,
    ),
    AdditionalWorkModeCountdownSpec(
        key="outside_remaining_time",
        translation_key="outside_remaining_time",
        param_name=PARAM_TIME_TO_END_OUTSIDE,
        param_id=PARAM_TIME_TO_END_OUTSIDE_ID,
    ),
    AdditionalWorkModeCountdownSpec(
        key="airing_remaining_time",
        translation_key="airing_remaining_time",
        param_name=PARAM_TIME_TO_END_AIRING,
        param_id=PARAM_TIME_TO_END_AIRING_ID,
    ),
)


def resolve_additional_work_mode_number(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    spec: AdditionalWorkModeNumberSpec,
    data_index: EditParamIndex | None = None,
) -> NumberParamStatus:
    """Validate identity and resolve the live value for a preset number."""
    return resolve_writable_number_param(
        reg_params,
        edit_params,
        name=spec.param_name,
        expected_id=spec.param_id,
        fallback_min=spec.fallback_min,
        fallback_max=spec.fallback_max,
        data_index=data_index,
    )


def resolve_additional_work_mode_countdown(
    edit_params: dict[str, Any],
    spec: AdditionalWorkModeCountdownSpec,
    data_index: EditParamIndex | None = None,
) -> NumberParamStatus:
    """Resolve remaining minutes for an active additional work mode."""
    return resolve_readonly_number_param(
        edit_params,
        name=spec.param_name,
        expected_id=spec.param_id,
        data_index=data_index,
    )
