"""Supply and exhaust fan speed sensors."""

from __future__ import annotations

from typing import override

from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import PERCENTAGE

from ..const import PARAM_EXHAUST_FAN_SPEED, PARAM_SUPPLY_FAN_SPEED
from .descriptions import PlumEconetSensorEntityDescription
from .entity import PlumEconetSensor

ICON_FAN = "mdi:fan"
ICON_FAN_OFF = "mdi:fan-off"

FAN_SENSORS: tuple[PlumEconetSensorEntityDescription, ...] = (
    PlumEconetSensorEntityDescription(
        key="supply_fan_speed",
        translation_key="supply_fan_speed",
        param_name=PARAM_SUPPLY_FAN_SPEED,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PlumEconetSensorEntityDescription(
        key="exhaust_fan_speed",
        translation_key="exhaust_fan_speed",
        param_name=PARAM_EXHAUST_FAN_SPEED,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


class PlumEconetFanSpeedSensor(PlumEconetSensor):
    """Fan speed sensor with running/stopped icons."""

    @property
    @override
    def icon(self) -> str:
        """Return mdi:fan when running, mdi:fan-off when stopped."""
        speed = self._parsed_value()
        if speed is not None and speed != 0.0:
            return ICON_FAN
        return ICON_FAN_OFF
