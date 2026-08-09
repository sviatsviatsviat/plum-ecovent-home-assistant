"""Sensor platform for Plum ecoVENT."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .. import PlumEconetConfigEntry
from ..models.additional_work_presets import ADDITIONAL_WORK_MODE_COUNTDOWNS
from .additional_work_mode import PlumEconetAdditionalWorkModeCountdownSensor
from .bypass import PlumEconetBypassMotorStateSensor, PlumEconetBypassOpenLevelSensor
from .entity import PlumEconetSensor
from .fan import FAN_SENSORS, PlumEconetFanSpeedSensor
from .filter import FILTER_SENSORS, PlumEconetFilterSensor
from .temperature import TEMPERATURE_SENSORS
from .wifi import WIFI_SENSORS, PlumEconetWifiSensor
from .work_status import (
    WORK_STATUS_ENUM_SENSORS,
    WORK_STATUS_TEMP_SENSORS,
    PlumEconetWorkStatusEnumSensor,
    PlumEconetWorkStatusTempSensor,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PlumEconetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Plum ecoVENT sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            *(
                PlumEconetFanSpeedSensor(coordinator, description)
                for description in FAN_SENSORS
            ),
            *(
                PlumEconetSensor(coordinator, description)
                for description in TEMPERATURE_SENSORS
            ),
            *(
                PlumEconetFilterSensor(coordinator, description)
                for description in FILTER_SENSORS
            ),
            *(
                PlumEconetWorkStatusTempSensor(coordinator, description)
                for description in WORK_STATUS_TEMP_SENSORS
            ),
            *(
                PlumEconetWorkStatusEnumSensor(coordinator, description)
                for description in WORK_STATUS_ENUM_SENSORS
            ),
            PlumEconetBypassMotorStateSensor(coordinator),
            PlumEconetBypassOpenLevelSensor(coordinator),
            *(
                PlumEconetWifiSensor(coordinator, description)
                for description in WIFI_SENSORS
            ),
            *(
                PlumEconetAdditionalWorkModeCountdownSensor(coordinator, spec)
                for spec in ADDITIONAL_WORK_MODE_COUNTDOWNS
            ),
        ]
    )
