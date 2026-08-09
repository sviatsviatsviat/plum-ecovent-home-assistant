"""Base number for writable editParams.data numeric setpoints."""

from __future__ import annotations

from typing import ClassVar, override

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.exceptions import HomeAssistantError

from ..entity import PlumEconetCoordinatorEntity
from ..exceptions import PlumEconetError
from ..parameters import EditableNumberStatus
from ..pending_write import PlumEconetPendingWriteMixin


class PlumEconetEditableNumber(
    PlumEconetPendingWriteMixin, PlumEconetCoordinatorEntity, NumberEntity
):
    """Number backed by a writable editParams.data entry."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 1.0
    _param_id: ClassVar[int]
    _label: ClassVar[str]
    _param_name: ClassVar[str]

    @property
    def _status(self) -> EditableNumberStatus:
        """Return the coordinator status for this number."""
        raise NotImplementedError

    @override
    def _pending_device_value(self) -> float | None:
        """Return the live setpoint from the device snapshot."""
        return self._status.value

    @property
    @override
    def available(self) -> bool:
        """Return True when identity and advertised numeric bounds validate."""
        status = self._status
        return (
            super().available
            and status.valid
            and status.min_value is not None
            and status.max_value is not None
        )

    @property
    @override
    def native_value(self) -> float | None:
        """Return pending setpoint while applying, else the live value."""
        return self.effective_value(self._status.value)

    @property
    @override
    def native_min_value(self) -> float:
        """Return the module-advertised minimum."""
        status = self._status
        if status.valid and status.min_value is not None:
            return status.min_value
        return 0.0

    @property
    @override
    def native_max_value(self) -> float:
        """Return the module-advertised maximum."""
        status = self._status
        if status.valid and status.max_value is not None:
            return status.max_value
        return 0.0

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Write a numeric setpoint via newParam after identity and range checks."""
        status = self._status
        if (
            not status.valid
            or status.min_value is None
            or status.max_value is None
        ):
            raise HomeAssistantError(
                f"{self._label} is unavailable; "
                f"{self._param_name} identity check failed"
            )

        if value < status.min_value or value > status.max_value:
            raise HomeAssistantError(
                f"{self._param_name} value {value} is outside "
                f"allowed range {status.min_value}–{status.max_value}"
            )

        # Module setpoints use integer wires (minv/maxv are whole degrees).
        wire = int(round(value))
        write_seq = self.begin_write()
        try:
            await self.coordinator.async_set_param(self._param_id, wire)
        except PlumEconetError as err:
            raise HomeAssistantError(
                f"Failed to set {self._label.lower()} to {wire}: {err}"
            ) from err

        if self.set_pending(float(wire), write_seq=write_seq):
            self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
