"""Base number for spec-driven writable parameters."""

from __future__ import annotations

from typing import Protocol, override

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory

from ..coordinator import PlumEconetCoordinator
from ..entity import PlumEconetCoordinatorEntity
from ..exceptions import PlumEconetError
from ..parameters import NumberParamStatus
from ..pending_write import PlumEconetPendingWriteMixin


class _NumberSpec(Protocol):
    """Minimal spec surface shared by User Mode and additional-mode numbers."""

    key: str
    translation_key: str
    icon: str
    unit: str
    param_name: str
    fallback_min: float
    fallback_max: float


class PlumEconetSpecNumber(
    PlumEconetPendingWriteMixin, PlumEconetCoordinatorEntity, NumberEntity
):
    """Number driven by a param spec with module or fallback bounds."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 1.0

    def __init__(
        self,
        coordinator: PlumEconetCoordinator,
        spec: _NumberSpec,
    ) -> None:
        """Initialize the number from a writable-param spec."""
        description = NumberEntityDescription(
            key=spec.key,
            translation_key=spec.translation_key,
            icon=spec.icon,
            native_unit_of_measurement=spec.unit,
            entity_category=EntityCategory.CONFIG,
            device_class=(
                NumberDeviceClass.TEMPERATURE
                if spec.unit == UnitOfTemperature.CELSIUS
                else None
            ),
        )
        super().__init__(coordinator, description)
        self._spec = spec

    def _resolve(self) -> NumberParamStatus:
        """Return the coordinator-resolved status for this spec."""
        raise NotImplementedError

    @property
    def _status(self) -> NumberParamStatus:
        """Return the resolved status for this parameter."""
        return self._resolve()

    @override
    def _pending_device_value(self) -> float | None:
        """Return the live numeric value from the device snapshot."""
        return self._status.value

    @property
    @override
    def available(self) -> bool:
        """Return True when identity and live value validate."""
        return super().available and self._status.valid

    @property
    @override
    def native_value(self) -> float | None:
        """Return pending value while applying, else the live value."""
        return self.effective_value(self._status.value)

    @property
    @override
    def native_min_value(self) -> float:
        """Return minv from the module when present, else the documented range."""
        status = self._status
        if status.valid and status.min_value is not None:
            return status.min_value
        return self._spec.fallback_min

    @property
    @override
    def native_max_value(self) -> float:
        """Return maxv from the module when present, else the documented range."""
        status = self._status
        if status.valid and status.max_value is not None:
            return status.max_value
        return self._spec.fallback_max

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Write the value via newParam after identity and range checks."""
        status = self._status
        if not status.valid or status.param_id is None:
            raise HomeAssistantError(
                f"{self._spec.param_name} is unavailable; identity check failed"
            )

        min_value = (
            status.min_value
            if status.min_value is not None
            else self._spec.fallback_min
        )
        max_value = (
            status.max_value
            if status.max_value is not None
            else self._spec.fallback_max
        )
        if value < min_value or value > max_value:
            raise HomeAssistantError(
                f"{self._spec.param_name} value {value} is outside "
                f"allowed range {min_value}–{max_value}"
            )

        # Modules expect integer wire values for these params (mult 1).
        wire = int(round(value))
        write_seq = self.begin_write()
        try:
            await self.coordinator.async_set_param(status.param_id, wire)
        except PlumEconetError as err:
            raise HomeAssistantError(
                f"Failed to set {self._spec.param_name} to {wire}: {err}"
            ) from err

        if self.set_pending(float(wire), write_seq=write_seq):
            self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
