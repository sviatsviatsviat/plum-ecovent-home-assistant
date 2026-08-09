"""Current work status sensors from informationParams slots 101–105."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.helpers.typing import StateType

from ..entity import PlumEconetCoordinatorEntity
from ..models.work import (
    ATTR_COMFORT_TEMPERATURE,
    ATTR_CONTROL_MODE_OPTION,
    ATTR_EXTERNAL_TEMPERATURE,
    ATTR_LEADING_TEMPERATURE,
    ATTR_SEASON_STATUS_OPTION,
    CONTROL_MODES,
    COORDINATOR_ATTR_WORK_STATUS,
    OPTION_UNSUPPORTED,
    SEASON_STATUSES,
)
from .attr import (
    PlumEconetAttrNumericSensor,
    PlumEconetAttrNumericSensorEntityDescription,
)

ICON_CONTROL_MODE = "mdi:thermometer-lines"
ICON_SEASON_STATUS = "mdi:sun-snowflake-variant"


@dataclass(frozen=True, kw_only=True)
class PlumEconetWorkStatusTempEntityDescription(
    PlumEconetAttrNumericSensorEntityDescription
):
    """Describes a Current work status temperature sensor."""

    value_attr: Literal[
        ATTR_COMFORT_TEMPERATURE,
        ATTR_LEADING_TEMPERATURE,
        ATTR_EXTERNAL_TEMPERATURE,
    ]


@dataclass(frozen=True, kw_only=True)
class PlumEconetWorkStatusEnumEntityDescription(SensorEntityDescription):
    """Describes a Current work status enum sensor."""

    option_attr: Literal[ATTR_CONTROL_MODE_OPTION, ATTR_SEASON_STATUS_OPTION]


WORK_STATUS_TEMP_SENSORS: tuple[PlumEconetWorkStatusTempEntityDescription, ...] = (
    PlumEconetWorkStatusTempEntityDescription(
        key="current_comfort_temperature",
        translation_key="current_comfort_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer-check",
        value_attr=ATTR_COMFORT_TEMPERATURE,
    ),
    PlumEconetWorkStatusTempEntityDescription(
        key="current_leading_temperature",
        translation_key="current_leading_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer-auto",
        value_attr=ATTR_LEADING_TEMPERATURE,
    ),
    PlumEconetWorkStatusTempEntityDescription(
        key="external_temperature",
        translation_key="external_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:home-thermometer",
        value_attr=ATTR_EXTERNAL_TEMPERATURE,
    ),
)

WORK_STATUS_ENUM_SENSORS: tuple[PlumEconetWorkStatusEnumEntityDescription, ...] = (
    PlumEconetWorkStatusEnumEntityDescription(
        key="control_mode",
        translation_key="control_mode",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=[*(mode.option for mode in CONTROL_MODES), OPTION_UNSUPPORTED],
        option_attr=ATTR_CONTROL_MODE_OPTION,
        icon=ICON_CONTROL_MODE,
    ),
    PlumEconetWorkStatusEnumEntityDescription(
        key="summer_winter_status",
        translation_key="summer_winter_status",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=[*(mode.option for mode in SEASON_STATUSES), OPTION_UNSUPPORTED],
        option_attr=ATTR_SEASON_STATUS_OPTION,
        icon=ICON_SEASON_STATUS,
    ),
)


class PlumEconetWorkStatusTempSensor(PlumEconetAttrNumericSensor):
    """Temperature sensor from Current work status informationParams slots."""

    entity_description: PlumEconetWorkStatusTempEntityDescription
    _coordinator_snapshot_attr: ClassVar[str] = COORDINATOR_ATTR_WORK_STATUS


class PlumEconetWorkStatusEnumSensor(PlumEconetCoordinatorEntity, SensorEntity):
    """Enum sensor from Current work status informationParams mode slots."""

    entity_description: PlumEconetWorkStatusEnumEntityDescription

    def _option(self) -> str | None:
        """Return the mapped option key, Unsupported, or None if missing."""
        return getattr(
            self.coordinator.work_status,
            self.entity_description.option_attr,
        )

    @property
    @override
    def available(self) -> bool:
        """Return True when the informationParams mode slot parses."""
        return super().available and self._option() is not None

    @property
    @override
    def native_value(self) -> StateType:
        """Return the enum option key."""
        return self._option()
