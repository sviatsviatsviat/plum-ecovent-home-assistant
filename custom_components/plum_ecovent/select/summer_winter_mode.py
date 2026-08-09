"""Summer / winter mode select (REKWS2)."""

from __future__ import annotations

from typing import override

from homeassistant.components.select import SelectEntityDescription
from homeassistant.helpers.entity import EntityCategory

from ..const import PARAM_SUMMER_WINTER_MODE, PARAM_SUMMER_WINTER_MODE_ID
from ..coordinator import PlumEconetCoordinator
from ..models.summer_winter import SUMMER_WINTER_MODES, SummerWinterMode
from ..parameters import MappedParamStatus
from .entity import PlumEconetMappedSelect

SUMMER_WINTER_MODE_DESCRIPTION = SelectEntityDescription(
    key="summer_winter_mode",
    translation_key="summer_winter_mode",
    icon="mdi:sun-snowflake-variant",
    entity_category=EntityCategory.CONFIG,
)


class PlumEconetSummerWinterModeSelect(PlumEconetMappedSelect):
    """Summer / winter mode (Summer / Winter / Auto / Ventilation) from REKWS2."""

    entity_description = SUMMER_WINTER_MODE_DESCRIPTION
    _modes = SUMMER_WINTER_MODES
    _param_id = PARAM_SUMMER_WINTER_MODE_ID
    _label = "Summer / winter mode"
    _param_name = PARAM_SUMMER_WINTER_MODE
    _mode_cls = SummerWinterMode

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the select."""
        super().__init__(coordinator, SUMMER_WINTER_MODE_DESCRIPTION)

    @property
    @override
    def _status(self) -> MappedParamStatus:
        """Return REKWS2 status from the coordinator."""
        return self.coordinator.summer_winter_mode
