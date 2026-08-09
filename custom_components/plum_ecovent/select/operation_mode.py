"""Recuperation operation mode select (REKWS1)."""

from __future__ import annotations

from typing import override

from homeassistant.components.select import SelectEntityDescription

from ..const import PARAM_OPERATION_MODE, PARAM_OPERATION_MODE_ID
from ..coordinator import PlumEconetCoordinator
from ..models.operation import OPERATION_MODES, OperationMode
from ..parameters import MappedParamStatus
from .entity import PlumEconetMappedSelect

OPERATION_MODE_DESCRIPTION = SelectEntityDescription(
    key="operation_mode",
    translation_key="operation_mode",
    icon="mdi:tune",
)


class PlumEconetOperationModeSelect(PlumEconetMappedSelect):
    """Recuperation operation mode (Halt + Mode 1–4) from REKWS1."""

    entity_description = OPERATION_MODE_DESCRIPTION
    _modes = OPERATION_MODES
    _param_id = PARAM_OPERATION_MODE_ID
    _label = "Operation mode"
    _param_name = PARAM_OPERATION_MODE
    _mode_cls = OperationMode

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the select."""
        super().__init__(coordinator, OPERATION_MODE_DESCRIPTION)

    @property
    @override
    def _status(self) -> MappedParamStatus:
        """Return REKWS1 status from the coordinator."""
        return self.coordinator.operation_mode
