"""Filter replacement interval number (FILTERtimeToAlarm)."""

from __future__ import annotations

from typing import override

from homeassistant.components.number import NumberEntityDescription, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from ..const import PARAM_FILTER_TIME_TO_ALARM, PARAM_FILTER_TIME_TO_ALARM_ID
from ..coordinator import PlumEconetCoordinator
from ..parameters import EditableNumberStatus
from .entity import PlumEconetEditableNumber

FILTER_TIME_TO_ALARM_DESCRIPTION = NumberEntityDescription(
    key="filter_time_to_alarm",
    translation_key="filter_time_to_alarm",
    icon="mdi:air-filter",
    native_unit_of_measurement=UnitOfTime.DAYS,
    native_step=1,
    entity_category=EntityCategory.CONFIG,
)


class PlumEconetFilterTimeToAlarmNumber(PlumEconetEditableNumber):
    """Days of filter operation before the replacement alert."""

    entity_description = FILTER_TIME_TO_ALARM_DESCRIPTION
    # 1–1500 days is too wide for a slider to land on exact values.
    _attr_mode = NumberMode.BOX
    _param_id = PARAM_FILTER_TIME_TO_ALARM_ID
    _label = "Filter replacement interval"
    _param_name = PARAM_FILTER_TIME_TO_ALARM

    def __init__(self, coordinator: PlumEconetCoordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator, FILTER_TIME_TO_ALARM_DESCRIPTION)

    @property
    @override
    def _status(self) -> EditableNumberStatus:
        """Return FILTERtimeToAlarm status from the coordinator."""
        return self.coordinator.filter_time_to_alarm
