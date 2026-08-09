"""Read-only remaining-time sensors for Party / Outside / Airing."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.helpers.typing import StateType

from ..entity import PlumEconetCoordinatorEntity
from ..models.additional_work_presets import (
    AdditionalWorkModeCountdownSpec,
)
from ..parameters import NumberParamStatus

if TYPE_CHECKING:
    from ..coordinator import PlumEconetCoordinator

ICON_TIMER = "mdi:timer-sand"
ICON_TIMER_IDLE = "mdi:timer-sand-complete"


class PlumEconetAdditionalWorkModeCountdownSensor(
    PlumEconetCoordinatorEntity, SensorEntity
):
    """Remaining minutes while an additional / timed work mode is active.

    Party and Outside advertise ``unit`` ``4`` (hours) in editParams, but the
    live countdown is observed in minutes (same as Airing). Idle modules
    report ``-1``, which this sensor presents as ``0``.
    """

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PlumEconetCoordinator,
        spec: AdditionalWorkModeCountdownSpec,
    ) -> None:
        """Initialize the countdown sensor."""
        description = SensorEntityDescription(
            key=spec.key,
            translation_key=spec.translation_key,
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.MINUTES,
            state_class=SensorStateClass.MEASUREMENT,
        )
        super().__init__(coordinator, description)
        self._spec = spec

    @property
    def _status(self) -> NumberParamStatus:
        """Return remaining-time status from editParams."""
        return self.coordinator.number_status(self._spec.param_name)

    @property
    @override
    def available(self) -> bool:
        """Return True when identity validates (including idle ``0``)."""
        return super().available and self._status.valid

    @property
    @override
    def native_value(self) -> StateType:
        """Return remaining minutes (``0`` when idle)."""
        return self._status.value

    @property
    @override
    def icon(self) -> str:
        """Return timer-sand when counting down, timer-sand-complete when idle."""
        remaining = self._status.value
        if remaining is not None and remaining > 0.0:
            return ICON_TIMER
        return ICON_TIMER_IDLE
