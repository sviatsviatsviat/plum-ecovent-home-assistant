"""Select platform for Plum ecoVENT."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .. import PlumEconetConfigEntry
from .additional_work_mode import PlumEconetAdditionalWorkModeSelect
from .bypass_mode import PlumEconetBypassModeSelect
from .operation_mode import PlumEconetOperationModeSelect
from .summer_winter_mode import PlumEconetSummerWinterModeSelect


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PlumEconetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Plum ecoVENT select entities from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            PlumEconetBypassModeSelect(coordinator),
            PlumEconetSummerWinterModeSelect(coordinator),
            PlumEconetOperationModeSelect(coordinator),
            PlumEconetAdditionalWorkModeSelect(coordinator),
        ]
    )
