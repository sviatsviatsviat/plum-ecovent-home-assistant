"""Bypass mode select (BYPmodSett)."""

from __future__ import annotations

from typing import override

from homeassistant.components.select import SelectEntityDescription
from homeassistant.helpers.entity import EntityCategory

from ..const import PARAM_BYPASS_MODE, PARAM_BYPASS_MODE_ID
from ..coordinator import PlumEconetCoordinator
from ..models.bypass import BYPASS_MODES, BypassMode
from ..parameters import MappedParamStatus
from .entity import PlumEconetMappedSelect

BYPASS_MODE_DESCRIPTION = SelectEntityDescription(
    key="bypass_mode",
    translation_key="bypass_mode",
    icon="mdi:valve",
    entity_category=EntityCategory.CONFIG,
)


class PlumEconetBypassModeSelect(PlumEconetMappedSelect):
    """Bypass mode (Auto / Open / Close) from BYPmodSett."""

    entity_description = BYPASS_MODE_DESCRIPTION
    _modes = BYPASS_MODES
    _param_id = PARAM_BYPASS_MODE_ID
    _label = "Bypass mode"
    _param_name = PARAM_BYPASS_MODE
    _mode_cls = BypassMode

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the select."""
        super().__init__(coordinator, BYPASS_MODE_DESCRIPTION)

    @property
    @override
    def _status(self) -> MappedParamStatus:
        """Return BYPmodSett status from the coordinator."""
        return self.coordinator.bypass_mode
