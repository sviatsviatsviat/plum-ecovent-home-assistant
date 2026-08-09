"""Data update coordinator for Plum ecoVENT."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..api import PlumEconetApi
from ..const import (
    DEFAULT_REG_REFRESH,
    DOMAIN,
    PARAM_ADDITIONAL_WORK_MODE,
    PARAM_BYPASS_MODE,
    PARAM_OPERATION_MODE,
    PARAM_SUMMER_WINTER_MODE,
)
from ..exceptions import PlumEconetAuthError, PlumEconetError
from ..models.additional_work import (
    AdditionalWorkMode,
    AdditionalWorkModeStatus,
)
from ..models.bypass import BypassMode, BypassModeStatus
from ..models.filter import FilterStatus
from ..models.operation import OperationMode, OperationModeStatus
from ..models.summer_winter import SummerWinterMode, SummerWinterModeStatus
from ..models.work import WorkStatus
from ..parameters import (
    EditableNumberStatus,
    EditParamIndex,
    MappedParamStatus,
    NumberParamStatus,
)
from .snapshot import PlumEconetData, build_snapshot

_LOGGER = logging.getLogger(__name__)


class PlumEconetCoordinator(DataUpdateCoordinator[PlumEconetData]):
    """Poll and validate one atomic ecoNET data snapshot each cycle."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: PlumEconetApi,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_REG_REFRESH),
        )
        self._api = api
        self._expected_uid = config_entry.unique_id
        self._unexpected_wires: dict[str, int] = {}

    @property
    def sys_params(self) -> dict[str, Any]:
        """Return the latest validated sysParams payload."""
        return self.data.sys_params if self.data is not None else {}

    @property
    def reg_params(self) -> dict[str, Any]:
        """Return the latest validated regParams payload."""
        return self.data.reg_params if self.data is not None else {}

    @property
    def edit_params(self) -> dict[str, Any]:
        """Return the latest validated editParams payload."""
        return self.data.edit_params if self.data is not None else {}

    @property
    def edit_param_index(self) -> EditParamIndex:
        """Return the latest editParams entries indexed by name."""
        return self.data.edit_param_index if self.data is not None else {}

    @property
    def filter_status(self) -> FilterStatus:
        """Return the latest validated filter status."""
        if self.data is not None:
            return self.data.filter_status
        return FilterStatus(None, None, None, None, None, None)

    @property
    def work_status(self) -> WorkStatus:
        """Return the latest validated work status."""
        return self.data.work_status if self.data is not None else WorkStatus(
            None, None, None, None, None
        )

    @property
    def operation_mode(self) -> OperationModeStatus:
        """Return the latest validated operation mode."""
        return self.data.operation_mode if self.data is not None else (
            OperationModeStatus.invalid(OperationMode)
        )

    @property
    def additional_work_mode(self) -> AdditionalWorkModeStatus:
        """Return the latest validated additional work mode."""
        return self.data.additional_work_mode if self.data is not None else (
            AdditionalWorkModeStatus.invalid(AdditionalWorkMode)
        )

    @property
    def summer_winter_mode(self) -> SummerWinterModeStatus:
        """Return the latest validated summer / winter mode."""
        return self.data.summer_winter_mode if self.data is not None else (
            SummerWinterModeStatus.invalid(SummerWinterMode)
        )

    @property
    def winter_active_temp(self) -> EditableNumberStatus:
        """Return the latest validated winter activation temperature."""
        return self.data.winter_active_temp if self.data is not None else (
            EditableNumberStatus.invalid()
        )

    @property
    def summer_hysteresis(self) -> EditableNumberStatus:
        """Return the latest validated summer hysteresis."""
        return self.data.summer_hysteresis if self.data is not None else (
            EditableNumberStatus.invalid()
        )

    @property
    def bypass_mode(self) -> BypassModeStatus:
        """Return the latest validated bypass mode."""
        return self.data.bypass_mode if self.data is not None else (
            BypassModeStatus.invalid(BypassMode)
        )

    def number_status(self, param_name: str) -> NumberParamStatus:
        """Return one precomputed writable or countdown number status."""
        if self.data is None:
            return NumberParamStatus.invalid()
        return self.data.number_statuses.get(param_name, NumberParamStatus.invalid())

    async def async_set_param(self, param_id: int, value: int) -> None:
        """Write a parameter through the coordinator-owned API client."""
        await self._api.async_set_param(str(param_id), value)

    def _validate_identity(self, sys_params: dict[str, Any]) -> None:
        """Reject missing or changed module identity before accepting data."""
        uid = sys_params.get("uid")
        if not uid:
            message = "The ecoNET module did not return a device uid in sysParams."
        elif self._expected_uid is not None and str(uid) != str(self._expected_uid):
            message = (
                "The ecoNET module uid does not match this config entry; "
                "refusing data from a different device."
            )
        else:
            return

        if self.data is None:
            raise ConfigEntryError(message)
        raise UpdateFailed(message)

    def _log_unexpected_wires(self, data: PlumEconetData) -> None:
        """Warn once when a parameter enters a new unsupported wire state."""
        statuses: tuple[tuple[str, MappedParamStatus], ...] = (
            (PARAM_OPERATION_MODE, data.operation_mode),
            (PARAM_ADDITIONAL_WORK_MODE, data.additional_work_mode),
            (PARAM_SUMMER_WINTER_MODE, data.summer_winter_mode),
            (PARAM_BYPASS_MODE, data.bypass_mode),
        )
        unexpected = {
            name: status.wire
            for name, status in statuses
            if status.valid and status.wire is not None and status.mode is None
        }
        for name, wire in unexpected.items():
            if self._unexpected_wires.get(name) == wire:
                continue
            _LOGGER.warning(
                "Unexpected %s wire value %s; reporting as Unsupported",
                name,
                wire,
            )
        self._unexpected_wires = unexpected

    async def _async_update_data(self) -> PlumEconetData:
        """Fetch and atomically publish one validated module snapshot."""
        first_update = self.data is None
        try:
            sys_params = await self._api.async_get_sys_params()
            self._validate_identity(sys_params)
            reg_params = await self._api.async_get_reg_params()
            edit_params = await self._api.async_get_edit_params()
            data = build_snapshot(sys_params, reg_params, edit_params)
        except PlumEconetAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PlumEconetError as err:
            raise UpdateFailed(str(err)) from err

        if first_update:
            reg_refresh = sys_params.get("regRefresh", DEFAULT_REG_REFRESH)
            try:
                seconds = int(reg_refresh)
            except (TypeError, ValueError):
                seconds = DEFAULT_REG_REFRESH
            self.update_interval = timedelta(seconds=max(seconds, 1))

        self._log_unexpected_wires(data)
        return data
