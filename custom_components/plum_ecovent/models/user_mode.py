"""User Mode 1–4 fan velocity and preset temperature parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.const import PERCENTAGE, UnitOfTemperature

from ..const import (
    PARAM_USER_1_EXH_FAN_SPEED,
    PARAM_USER_1_EXH_FAN_SPEED_ID,
    PARAM_USER_1_SETPOINT,
    PARAM_USER_1_SETPOINT_ID,
    PARAM_USER_1_SUP_FAN_SPEED,
    PARAM_USER_1_SUP_FAN_SPEED_ID,
    PARAM_USER_2_EXH_FAN_SPEED,
    PARAM_USER_2_EXH_FAN_SPEED_ID,
    PARAM_USER_2_SETPOINT,
    PARAM_USER_2_SETPOINT_ID,
    PARAM_USER_2_SUP_FAN_SPEED,
    PARAM_USER_2_SUP_FAN_SPEED_ID,
    PARAM_USER_3_EXH_FAN_SPEED,
    PARAM_USER_3_EXH_FAN_SPEED_ID,
    PARAM_USER_3_SETPOINT,
    PARAM_USER_3_SETPOINT_ID,
    PARAM_USER_3_SUP_FAN_SPEED,
    PARAM_USER_3_SUP_FAN_SPEED_ID,
    PARAM_USER_4_EXH_FAN_SPEED,
    PARAM_USER_4_EXH_FAN_SPEED_ID,
    PARAM_USER_4_SETPOINT,
    PARAM_USER_4_SETPOINT_ID,
    PARAM_USER_4_SUP_FAN_SPEED,
    PARAM_USER_4_SUP_FAN_SPEED_ID,
)
from ..parameters import (
    EditParamIndex,
    NumberParamStatus,
    resolve_writable_number_param,
)

# Documented module ranges (§3.4 Related User Mode parameters).
USER_MODE_FAN_MIN = 20.0
USER_MODE_FAN_MAX = 100.0
USER_MODE_SETPOINT_MIN = 8.0
USER_MODE_SETPOINT_MAX = 30.0


@dataclass(frozen=True, slots=True, kw_only=True)
class UserModeNumberSpec:
    """Static definition for one User Mode number control."""

    key: str
    translation_key: str
    param_name: str
    param_id: int
    unit: str
    fallback_min: float
    fallback_max: float
    icon: str


USER_MODE_NUMBERS: tuple[UserModeNumberSpec, ...] = (
    UserModeNumberSpec(
        key="user_mode_1_supply_fan_speed",
        translation_key="user_mode_1_supply_fan_speed",
        param_name=PARAM_USER_1_SUP_FAN_SPEED,
        param_id=PARAM_USER_1_SUP_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
        icon="mdi:fan",
    ),
    UserModeNumberSpec(
        key="user_mode_1_exhaust_fan_speed",
        translation_key="user_mode_1_exhaust_fan_speed",
        param_name=PARAM_USER_1_EXH_FAN_SPEED,
        param_id=PARAM_USER_1_EXH_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
        icon="mdi:fan",
    ),
    UserModeNumberSpec(
        key="user_mode_1_preset_temperature",
        translation_key="user_mode_1_preset_temperature",
        param_name=PARAM_USER_1_SETPOINT,
        param_id=PARAM_USER_1_SETPOINT_ID,
        unit=UnitOfTemperature.CELSIUS,
        fallback_min=USER_MODE_SETPOINT_MIN,
        fallback_max=USER_MODE_SETPOINT_MAX,
        icon="mdi:thermometer",
    ),
    UserModeNumberSpec(
        key="user_mode_2_supply_fan_speed",
        translation_key="user_mode_2_supply_fan_speed",
        param_name=PARAM_USER_2_SUP_FAN_SPEED,
        param_id=PARAM_USER_2_SUP_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
        icon="mdi:fan",
    ),
    UserModeNumberSpec(
        key="user_mode_2_exhaust_fan_speed",
        translation_key="user_mode_2_exhaust_fan_speed",
        param_name=PARAM_USER_2_EXH_FAN_SPEED,
        param_id=PARAM_USER_2_EXH_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
        icon="mdi:fan",
    ),
    UserModeNumberSpec(
        key="user_mode_2_preset_temperature",
        translation_key="user_mode_2_preset_temperature",
        param_name=PARAM_USER_2_SETPOINT,
        param_id=PARAM_USER_2_SETPOINT_ID,
        unit=UnitOfTemperature.CELSIUS,
        fallback_min=USER_MODE_SETPOINT_MIN,
        fallback_max=USER_MODE_SETPOINT_MAX,
        icon="mdi:thermometer",
    ),
    UserModeNumberSpec(
        key="user_mode_3_supply_fan_speed",
        translation_key="user_mode_3_supply_fan_speed",
        param_name=PARAM_USER_3_SUP_FAN_SPEED,
        param_id=PARAM_USER_3_SUP_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
        icon="mdi:fan",
    ),
    UserModeNumberSpec(
        key="user_mode_3_exhaust_fan_speed",
        translation_key="user_mode_3_exhaust_fan_speed",
        param_name=PARAM_USER_3_EXH_FAN_SPEED,
        param_id=PARAM_USER_3_EXH_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
        icon="mdi:fan",
    ),
    UserModeNumberSpec(
        key="user_mode_3_preset_temperature",
        translation_key="user_mode_3_preset_temperature",
        param_name=PARAM_USER_3_SETPOINT,
        param_id=PARAM_USER_3_SETPOINT_ID,
        unit=UnitOfTemperature.CELSIUS,
        fallback_min=USER_MODE_SETPOINT_MIN,
        fallback_max=USER_MODE_SETPOINT_MAX,
        icon="mdi:thermometer",
    ),
    UserModeNumberSpec(
        key="user_mode_4_supply_fan_speed",
        translation_key="user_mode_4_supply_fan_speed",
        param_name=PARAM_USER_4_SUP_FAN_SPEED,
        param_id=PARAM_USER_4_SUP_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
        icon="mdi:fan",
    ),
    UserModeNumberSpec(
        key="user_mode_4_exhaust_fan_speed",
        translation_key="user_mode_4_exhaust_fan_speed",
        param_name=PARAM_USER_4_EXH_FAN_SPEED,
        param_id=PARAM_USER_4_EXH_FAN_SPEED_ID,
        unit=PERCENTAGE,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
        icon="mdi:fan",
    ),
    UserModeNumberSpec(
        key="user_mode_4_preset_temperature",
        translation_key="user_mode_4_preset_temperature",
        param_name=PARAM_USER_4_SETPOINT,
        param_id=PARAM_USER_4_SETPOINT_ID,
        unit=UnitOfTemperature.CELSIUS,
        fallback_min=USER_MODE_SETPOINT_MIN,
        fallback_max=USER_MODE_SETPOINT_MAX,
        icon="mdi:thermometer",
    ),
)


def resolve_user_mode_number(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
    spec: UserModeNumberSpec,
    data_index: EditParamIndex | None = None,
) -> NumberParamStatus:
    """Validate identity and resolve the live value for a User Mode number."""
    return resolve_writable_number_param(
        reg_params,
        edit_params,
        name=spec.param_name,
        expected_id=spec.param_id,
        fallback_min=spec.fallback_min,
        fallback_max=spec.fallback_max,
        data_index=data_index,
    )
