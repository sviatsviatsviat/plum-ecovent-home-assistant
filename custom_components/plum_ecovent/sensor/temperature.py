"""Primary air-path temperature sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature

from ..const import (
    PARAM_EXHAUST_AIR_TEMP,
    PARAM_EXTRACTED_AIR_TEMP,
    PARAM_INTAKE_AIR_TEMP,
    PARAM_SUPPLY_AIR_TEMP,
)
from .descriptions import PlumEconetSensorEntityDescription

TEMPERATURE_SENSORS: tuple[PlumEconetSensorEntityDescription, ...] = (
    PlumEconetSensorEntityDescription(
        key="supply_air_temperature",
        translation_key="supply_air_temperature",
        param_name=PARAM_SUPPLY_AIR_TEMP,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PlumEconetSensorEntityDescription(
        key="intake_air_temperature",
        translation_key="intake_air_temperature",
        param_name=PARAM_INTAKE_AIR_TEMP,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PlumEconetSensorEntityDescription(
        key="extracted_air_temperature",
        translation_key="extracted_air_temperature",
        param_name=PARAM_EXTRACTED_AIR_TEMP,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PlumEconetSensorEntityDescription(
        key="exhaust_air_temperature",
        translation_key="exhaust_air_temperature",
        param_name=PARAM_EXHAUST_AIR_TEMP,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
