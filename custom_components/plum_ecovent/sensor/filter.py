"""Filter depletion and operation-days sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal

from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime

from ..models.filter import (
    ATTR_EXTRACT_DAYS,
    ATTR_EXTRACT_DAYS_TO_ALERT,
    ATTR_EXTRACT_DEPLETION,
    ATTR_SUPPLY_DAYS,
    ATTR_SUPPLY_DAYS_TO_ALERT,
    ATTR_SUPPLY_DEPLETION,
    COORDINATOR_ATTR_FILTER_STATUS,
)
from .attr import (
    PlumEconetAttrNumericSensor,
    PlumEconetAttrNumericSensorEntityDescription,
)

ICON_AIR_FILTER = "mdi:air-filter"
ICON_CALENDAR_CLOCK = "mdi:calendar-clock"
ICON_ALARM = "mdi:clock-alert-outline"


@dataclass(frozen=True, kw_only=True)
class PlumEconetFilterSensorEntityDescription(
    PlumEconetAttrNumericSensorEntityDescription
):
    """Describes a filter sensor backed by validated informationParams slots."""

    value_attr: Literal[
        ATTR_SUPPLY_DEPLETION,
        ATTR_EXTRACT_DEPLETION,
        ATTR_SUPPLY_DAYS,
        ATTR_EXTRACT_DAYS,
        ATTR_SUPPLY_DAYS_TO_ALERT,
        ATTR_EXTRACT_DAYS_TO_ALERT,
    ]


FILTER_SENSORS: tuple[PlumEconetFilterSensorEntityDescription, ...] = (
    PlumEconetFilterSensorEntityDescription(
        key="supply_air_filter_depletion",
        translation_key="supply_air_filter_depletion",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_AIR_FILTER,
        value_attr=ATTR_SUPPLY_DEPLETION,
    ),
    PlumEconetFilterSensorEntityDescription(
        key="extracted_air_filter_depletion",
        translation_key="extracted_air_filter_depletion",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_AIR_FILTER,
        value_attr=ATTR_EXTRACT_DEPLETION,
    ),
    PlumEconetFilterSensorEntityDescription(
        key="supply_air_filter_operation_days",
        translation_key="supply_air_filter_operation_days",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_CALENDAR_CLOCK,
        value_attr=ATTR_SUPPLY_DAYS,
    ),
    PlumEconetFilterSensorEntityDescription(
        key="extracted_air_filter_operation_days",
        translation_key="extracted_air_filter_operation_days",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_CALENDAR_CLOCK,
        value_attr=ATTR_EXTRACT_DAYS,
    ),
    PlumEconetFilterSensorEntityDescription(
        key="supply_air_filter_days_to_alert",
        translation_key="supply_air_filter_days_to_alert",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon=ICON_ALARM,
        value_attr=ATTR_SUPPLY_DAYS_TO_ALERT,
    ),
    PlumEconetFilterSensorEntityDescription(
        key="extracted_air_filter_days_to_alert",
        translation_key="extracted_air_filter_days_to_alert",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon=ICON_ALARM,
        value_attr=ATTR_EXTRACT_DAYS_TO_ALERT,
    ),
)


class PlumEconetFilterSensor(PlumEconetAttrNumericSensor):
    """Filter status sensor from fixed, validated informationParams slots."""

    entity_description: PlumEconetFilterSensorEntityDescription
    _coordinator_snapshot_attr: ClassVar[str] = COORDINATOR_ATTR_FILTER_STATUS
