"""Base numeric sensor reading regParams.curr."""

from __future__ import annotations

from typing import override

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import StateType

from ..coordinator import PlumEconetCoordinator
from ..entity import PlumEconetEntity
from ..parameters.numeric import parse_finite_number
from .descriptions import PlumEconetSensorEntityDescription


class PlumEconetSensor(PlumEconetEntity, SensorEntity):
    """Sensor reading a numeric value from regParams.curr."""

    entity_description: PlumEconetSensorEntityDescription

    def __init__(
        self,
        coordinator: PlumEconetCoordinator,
        description: PlumEconetSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description, param_name=description.param_name)

    def _parsed_value(self) -> float | None:
        """Return a finite float from curr, or None if missing/invalid."""
        return parse_finite_number(self._curr_value())

    @property
    @override
    def available(self) -> bool:
        """Return True when the curr key exists and parses to a finite number."""
        return super().available and self._parsed_value() is not None

    @property
    @override
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self._parsed_value()
