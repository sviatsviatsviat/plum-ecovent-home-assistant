"""Additional / timed work mode select (REKWS4)."""

from __future__ import annotations

from typing import override

from homeassistant.components.select import SelectEntityDescription

from ..const import PARAM_ADDITIONAL_WORK_MODE, PARAM_ADDITIONAL_WORK_MODE_ID
from ..coordinator import PlumEconetCoordinator
from ..models.additional_work import ADDITIONAL_WORK_MODES, AdditionalWorkMode
from ..parameters import MappedParamStatus
from .entity import PlumEconetMappedSelect

ADDITIONAL_WORK_MODE_DESCRIPTION = SelectEntityDescription(
    key="additional_work_mode",
    translation_key="additional_work_mode",
    icon="mdi:clock-outline",
)


class PlumEconetAdditionalWorkModeSelect(PlumEconetMappedSelect):
    """Additional / timed work mode (Off / Outside / Party / Airing) from REKWS4."""

    entity_description = ADDITIONAL_WORK_MODE_DESCRIPTION
    _modes = ADDITIONAL_WORK_MODES
    _param_id = PARAM_ADDITIONAL_WORK_MODE_ID
    _label = "Additional work mode"
    _param_name = PARAM_ADDITIONAL_WORK_MODE
    _mode_cls = AdditionalWorkMode

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the select."""
        super().__init__(coordinator, ADDITIONAL_WORK_MODE_DESCRIPTION)

    @property
    @override
    def _status(self) -> MappedParamStatus:
        """Return REKWS4 status from the coordinator."""
        return self.coordinator.additional_work_mode
