"""Numeric sensors reading a named attribute from a coordinator snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.typing import StateType

from ..entity import PlumEconetCoordinatorEntity
from ..parameters.numeric import parse_finite_number


@dataclass(frozen=True, kw_only=True)
class PlumEconetAttrNumericSensorEntityDescription(SensorEntityDescription):
    """Describes a numeric sensor backed by an attribute on a coordinator snapshot."""

    value_attr: str


class PlumEconetAttrNumericSensor(PlumEconetCoordinatorEntity, SensorEntity):
    """Numeric sensor from ``getattr(coordinator.<snapshot>, value_attr)``."""

    entity_description: PlumEconetAttrNumericSensorEntityDescription
    _coordinator_snapshot_attr: ClassVar[str]

    def _parsed_value(self) -> float | None:
        """Return a finite float from the snapshot attribute, or None."""
        snapshot = getattr(self.coordinator, self._coordinator_snapshot_attr)
        return parse_finite_number(getattr(snapshot, self.entity_description.value_attr))

    @property
    @override
    def available(self) -> bool:
        """Return True when the snapshot attribute parses to a finite number."""
        return super().available and self._parsed_value() is not None

    @property
    @override
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self._parsed_value()
