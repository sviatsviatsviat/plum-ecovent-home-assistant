"""Number platform for Plum ecoVENT."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .. import PlumEconetConfigEntry
from ..models.additional_work_presets import ADDITIONAL_WORK_MODE_NUMBERS
from ..models.user_mode import USER_MODE_NUMBERS
from .additional_work_mode import PlumEconetAdditionalWorkModeNumber
from .summer_winter import (
    PlumEconetSummerHysteresisNumber,
    PlumEconetWinterActiveTempNumber,
)
from .user_mode import PlumEconetUserModeNumber


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PlumEconetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Plum ecoVENT number entities from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            PlumEconetSummerHysteresisNumber(coordinator),
            PlumEconetWinterActiveTempNumber(coordinator),
            *(
                PlumEconetAdditionalWorkModeNumber(coordinator, spec)
                for spec in ADDITIONAL_WORK_MODE_NUMBERS
            ),
            *(
                PlumEconetUserModeNumber(coordinator, spec)
                for spec in USER_MODE_NUMBERS
            ),
        ]
    )
