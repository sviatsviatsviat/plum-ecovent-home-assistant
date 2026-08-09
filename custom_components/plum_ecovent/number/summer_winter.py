"""Summer / winter related number setpoints."""

from __future__ import annotations

from typing import override

from homeassistant.components.number import NumberDeviceClass, NumberEntityDescription
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory

from ..const import (
    PARAM_SUMMER_HYSTERESIS,
    PARAM_SUMMER_HYSTERESIS_ID,
    PARAM_WINTER_ACTIVE_TEMP,
    PARAM_WINTER_ACTIVE_TEMP_ID,
)
from ..coordinator import PlumEconetCoordinator
from ..parameters import EditableNumberStatus
from .entity import PlumEconetEditableNumber

WINTER_ACTIVE_TEMP_DESCRIPTION = NumberEntityDescription(
    key="winter_active_temperature",
    translation_key="winter_active_temperature",
    icon="mdi:snowflake-thermometer",
    device_class=NumberDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    native_step=1,
    entity_category=EntityCategory.CONFIG,
)

SUMMER_HYSTERESIS_DESCRIPTION = NumberEntityDescription(
    key="summer_mode_hysteresis",
    translation_key="summer_mode_hysteresis",
    icon="mdi:sun-thermometer",
    # ecoNET names this "hysteresis", but the module exposes it like the winter
    # turn-on threshold (absolute °C setpoint), not a temperature delta.
    device_class=NumberDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    native_step=1,
    entity_category=EntityCategory.CONFIG,
)


class PlumEconetWinterActiveTempNumber(PlumEconetEditableNumber):
    """Winter mode turn-on temperature (REKwinterActiveTemp)."""

    entity_description = WINTER_ACTIVE_TEMP_DESCRIPTION
    _param_id = PARAM_WINTER_ACTIVE_TEMP_ID
    _label = "Winter mode turn-on temperature"
    _param_name = PARAM_WINTER_ACTIVE_TEMP

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator, WINTER_ACTIVE_TEMP_DESCRIPTION)

    @property
    @override
    def _status(self) -> EditableNumberStatus:
        """Return winter active temp status from the coordinator."""
        return self.coordinator.winter_active_temp


class PlumEconetSummerHysteresisNumber(PlumEconetEditableNumber):
    """Hysteresis for turning on summer mode (REKsummerHyst)."""

    entity_description = SUMMER_HYSTERESIS_DESCRIPTION
    _param_id = PARAM_SUMMER_HYSTERESIS_ID
    _label = "Summer mode hysteresis"
    _param_name = PARAM_SUMMER_HYSTERESIS

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator, SUMMER_HYSTERESIS_DESCRIPTION)

    @property
    @override
    def _status(self) -> EditableNumberStatus:
        """Return summer hysteresis status from the coordinator."""
        return self.coordinator.summer_hysteresis
