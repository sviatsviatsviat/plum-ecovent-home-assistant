"""Bypass companion sensors (motor state and open level)."""

from __future__ import annotations

from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.typing import StateType

from ..const import PARAM_BYPASS_OPEN_LEVEL
from ..coordinator import PlumEconetCoordinator
from ..entity import PlumEconetCoordinatorEntity
from ..models.bypass import (
    BYPASS_MOTOR_STATES,
    OPTION_UNSUPPORTED,
    resolve_bypass_motor_state_option,
)
from .descriptions import PlumEconetSensorEntityDescription
from .entity import PlumEconetSensor

ICON_BYPASS_MOTOR = "mdi:engine"
ICON_VALVE = "mdi:valve"
ICON_VALVE_OPEN = "mdi:valve-open"
ICON_VALVE_CLOSED = "mdi:valve-closed"

BYPASS_MOTOR_STATE_DESCRIPTION = SensorEntityDescription(
    key="bypass_motor_state",
    translation_key="bypass_motor_state",
    device_class=SensorDeviceClass.ENUM,
    options=[*(state.option for state in BYPASS_MOTOR_STATES), OPTION_UNSUPPORTED],
    icon=ICON_BYPASS_MOTOR,
)

BYPASS_OPEN_LEVEL_DESCRIPTION = PlumEconetSensorEntityDescription(
    key="bypass_open_level",
    translation_key="bypass_open_level",
    param_name=PARAM_BYPASS_OPEN_LEVEL,
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
)


class PlumEconetBypassMotorStateSensor(PlumEconetCoordinatorEntity, SensorEntity):
    """Bypass / Rotor motor state from BYPmodState in regParams.curr."""

    entity_description = BYPASS_MOTOR_STATE_DESCRIPTION

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, BYPASS_MOTOR_STATE_DESCRIPTION)

    def _option(self) -> str | None:
        """Return Off/On/Unsupported, or None when curr is missing/invalid."""
        return resolve_bypass_motor_state_option(self.coordinator.reg_params)

    @property
    @override
    def available(self) -> bool:
        """Return True when BYPmodState parses from curr."""
        return super().available and self._option() is not None

    @property
    @override
    def native_value(self) -> StateType:
        """Return the motor state option key."""
        return self._option()


class PlumEconetBypassOpenLevelSensor(PlumEconetSensor):
    """Bypass open level % from BYPcurControl in regParams.curr."""

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, BYPASS_OPEN_LEVEL_DESCRIPTION)

    @property
    @override
    def icon(self) -> str:
        """Return valve-closed at 0%, valve-open at 100%, else valve."""
        level = self._parsed_value()
        if level is None or level <= 0.0:
            return ICON_VALVE_CLOSED
        if level >= 100.0:
            return ICON_VALVE_OPEN
        return ICON_VALVE
