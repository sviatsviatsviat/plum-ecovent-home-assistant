"""Base select for writable curr-mapped wire enums."""

from __future__ import annotations

from typing import ClassVar, override

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError

from ..entity import PlumEconetCoordinatorEntity
from ..exceptions import PlumEconetError
from ..parameters import OPTION_UNSUPPORTED, MappedParamStatus, WireMappedIntEnum
from ..pending_write import PlumEconetPendingWriteMixin


class PlumEconetMappedSelect(
    PlumEconetPendingWriteMixin, PlumEconetCoordinatorEntity, SelectEntity
):
    """Select backed by a writable curr-mapped wire enum."""

    _modes: ClassVar[tuple[WireMappedIntEnum, ...]]
    _param_id: ClassVar[int]
    _label: ClassVar[str]
    _param_name: ClassVar[str]
    _mode_cls: ClassVar[type[WireMappedIntEnum]]

    @property
    def _status(self) -> MappedParamStatus:
        """Return the coordinator status for this select."""
        raise NotImplementedError

    @override
    def _pending_device_value(self) -> str | None:
        """Return the live option from the device snapshot."""
        return self._status.option

    @property
    @override
    def available(self) -> bool:
        """Return True when identity and curr value validate."""
        return super().available and self._status.valid

    @property
    @override
    def current_option(self) -> str | None:
        """Return pending option while applying, else the live wire option."""
        return self.effective_value(self._status.option)

    @property
    @override
    def options(self) -> list[str]:
        """Return writable modes, plus Unsupported when that is the live state."""
        opts = [mode.option for mode in self._modes]
        if self.current_option == OPTION_UNSUPPORTED:
            return [*opts, OPTION_UNSUPPORTED]
        return opts

    @override
    async def async_select_option(self, option: str) -> None:
        """Write a mapped wire value via newParam after identity checks."""
        status = self._status
        if not status.valid:
            raise HomeAssistantError(
                f"{self._label} is unavailable; "
                f"{self._param_name} identity check failed"
            )
        if option == OPTION_UNSUPPORTED:
            raise HomeAssistantError("Unsupported is read-only and cannot be selected")

        mode = self._mode_cls.from_option(option)
        if mode is None:
            raise HomeAssistantError(
                f"Unsupported {self._label.lower()} option: {option}"
            )

        write_seq = self.begin_write()
        try:
            await self.coordinator.async_set_param(self._param_id, mode.value)
        except PlumEconetError as err:
            raise HomeAssistantError(
                f"Failed to set {self._label.lower()} to {option}: {err}"
            ) from err

        if self.set_pending(option, write_seq=write_seq):
            self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
