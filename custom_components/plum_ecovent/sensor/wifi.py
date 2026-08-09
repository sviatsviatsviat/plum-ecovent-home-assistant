"""Wi-Fi link quality diagnostic sensors from sysParams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.helpers.typing import StateType

from ..coordinator import PlumEconetCoordinator
from ..entity import PlumEconetCoordinatorEntity
from ..models.wifi import (
    SYS_PARAM_QUALITY,
    SYS_PARAM_SIGNAL,
    parse_sys_param_number,
)


@dataclass(frozen=True, kw_only=True)
class PlumEconetWifiSensorEntityDescription(SensorEntityDescription):
    """Describes a diagnostic Wi-Fi sensor backed by a sysParams field."""

    sys_param_key: str


ICON_WIFI = "mdi:wifi"

WIFI_SENSORS: tuple[PlumEconetWifiSensorEntityDescription, ...] = (
    PlumEconetWifiSensorEntityDescription(
        key="wifi_signal",
        translation_key="wifi_signal",
        sys_param_key=SYS_PARAM_SIGNAL,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    PlumEconetWifiSensorEntityDescription(
        key="wifi_quality",
        translation_key="wifi_quality",
        sys_param_key=SYS_PARAM_QUALITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon=ICON_WIFI,
    ),
)


class PlumEconetWifiSensor(PlumEconetCoordinatorEntity, SensorEntity):
    """Diagnostic Wi-Fi sensor reading a numeric sysParams field."""

    entity_description: PlumEconetWifiSensorEntityDescription

    def __init__(
        self,
        coordinator: PlumEconetCoordinator,
        description: PlumEconetWifiSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)

    def _parsed_value(self) -> float | None:
        """Return a finite Wi-Fi metric, or None if missing/invalid."""
        return parse_sys_param_number(
            self.coordinator.sys_params.get(self.entity_description.sys_param_key)
        )

    @property
    @override
    def available(self) -> bool:
        """Return True when the sysParams field parses to a finite number."""
        return super().available and self._parsed_value() is not None

    @property
    @override
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self._parsed_value()
