"""Tests for Plum ecoVENT filter depletion and operation-days sensors."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.helpers import entity_registry as er

from custom_components.plum_ecovent.models.filter import resolve_filter_status
from tests.conftest import TEST_UID, setup_integration

SUPPLY_DEPL = "sensor.plum_ecovent_supply_air_filter_depletion"
EXTRACT_DEPL = "sensor.plum_ecovent_extracted_air_filter_depletion"
SUPPLY_DAYS = "sensor.plum_ecovent_supply_air_filter_operation_days"
EXTRACT_DAYS = "sensor.plum_ecovent_extracted_air_filter_operation_days"
SUPPLY_DAYS_TO_ALERT = "sensor.plum_ecovent_supply_air_filter_days_to_alert"
EXTRACT_DAYS_TO_ALERT = "sensor.plum_ecovent_extracted_air_filter_days_to_alert"

FILTER_ENTITIES = (
    SUPPLY_DEPL,
    EXTRACT_DEPL,
    SUPPLY_DAYS,
    EXTRACT_DAYS,
    SUPPLY_DAYS_TO_ALERT,
    EXTRACT_DAYS_TO_ALERT,
)


def _filter_edit_params() -> dict[str, Any]:
    """editParams fixture with fixed slots 61–64 and peer noise."""
    return {
        "editableParamsVer": 50,
        "data": {
            "574": {
                "name": "FILTERtimeToAlarm",
                "value": 180,
                "edit": True,
                "minv": 1,
                "maxv": 1500,
                "mult": 1,
                "unit": 0,
            },
            "34": {
                "name": "REKcurSupTemp",
                "value": 21.5,
                "edit": False,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 1,
            },
        },
        "informationParams": {
            "61": [True, [[61.67, 2, 0]]],
            "62": [True, [[61.67, 2, 0]]],
            "63": [True, [[111, 13, 0]]],
            "64": [True, [[111, 13, 0]]],
            # Peer noise — ignored because we only read 61–64.
            "52": [True, [[111, 13, 0]]],
            "55": [True, [[111, 13, 0]]],
            "71": [False, [[61.67, 2, 0]]],
            "72": [False, [[61.67, 2, 0]]],
        },
    }


async def test_resolve_filter_status_accepts_slots_matching_time_to_alarm() -> None:
    """Test fixed slots 61–64 validate against FILTERtimeToAlarm."""
    status = resolve_filter_status(_filter_edit_params())
    assert status.supply_depletion == 61.67
    assert status.extract_depletion == 61.67
    assert status.supply_days == 111.0
    assert status.extract_days == 111.0
    assert status.supply_days_to_alert == 69.0
    assert status.extract_days_to_alert == 69.0


def test_resolve_filter_status_rejects_mismatched_values() -> None:
    """Test slots that do not match FILTERtimeToAlarm become unavailable."""
    edit_params = _filter_edit_params()
    edit_params["informationParams"]["61"] = [True, [[10.0, 2, 0]]]
    edit_params["informationParams"]["62"] = [True, [[10.0, 2, 0]]]

    status = resolve_filter_status(edit_params)
    assert status.supply_depletion is None
    assert status.extract_depletion is None
    assert status.supply_days is None
    assert status.extract_days is None
    assert status.supply_days_to_alert is None
    assert status.extract_days_to_alert is None


def test_resolve_filter_status_requires_named_time_to_alarm() -> None:
    """Test validation fails when FILTERtimeToAlarm is absent."""
    edit_params = _filter_edit_params()
    edit_params["data"] = {"34": edit_params["data"]["34"]}
    status = resolve_filter_status(edit_params)
    assert status.supply_depletion is None
    assert status.extract_depletion is None
    assert status.supply_days is None
    assert status.extract_days is None
    assert status.supply_days_to_alert is None
    assert status.extract_days_to_alert is None


def test_resolve_filter_status_rejects_wrong_presentation_unit() -> None:
    """Test unexpected presentation units make the side unavailable."""
    edit_params = _filter_edit_params()
    edit_params["informationParams"]["61"] = [True, [[61.67, 6, 0]]]

    status = resolve_filter_status(edit_params)
    assert status.supply_depletion is None
    assert status.supply_days is None
    assert status.supply_days_to_alert is None
    assert status.extract_depletion == 61.67
    assert status.extract_days == 111.0
    assert status.extract_days_to_alert == 69.0


def test_resolve_filter_status_rejects_non_finite_time_to_alarm() -> None:
    """Test nan/inf FILTERtimeToAlarm values fail validation."""
    for bad_value in (math.nan, math.inf, -math.inf):
        edit_params = _filter_edit_params()
        edit_params["data"]["574"]["value"] = bad_value
        status = resolve_filter_status(edit_params)
        assert status.supply_depletion is None
        assert status.extract_depletion is None
        assert status.supply_days is None
        assert status.extract_days is None
        assert status.supply_days_to_alert is None
        assert status.extract_days_to_alert is None


def test_resolve_filter_status_rejects_non_finite_slot_values() -> None:
    """Test nan/inf informationParams values fail validation on each side."""
    supply_bad = _filter_edit_params()
    supply_bad["informationParams"]["61"] = [True, [[math.inf, 2, 0]]]
    supply_bad["informationParams"]["63"] = [True, [[math.nan, 13, 0]]]
    supply_status = resolve_filter_status(supply_bad)
    assert supply_status.supply_depletion is None
    assert supply_status.supply_days is None
    assert supply_status.supply_days_to_alert is None
    assert supply_status.extract_depletion == 61.67
    assert supply_status.extract_days == 111.0
    assert supply_status.extract_days_to_alert == 69.0

    extract_bad = _filter_edit_params()
    extract_bad["informationParams"]["62"] = [True, [[math.inf, 2, 0]]]
    extract_bad["informationParams"]["64"] = [True, [[math.nan, 13, 0]]]
    extract_status = resolve_filter_status(extract_bad)
    assert extract_status.extract_depletion is None
    assert extract_status.extract_days is None
    assert extract_status.extract_days_to_alert is None
    assert extract_status.supply_depletion == 61.67
    assert extract_status.supply_days == 111.0
    assert extract_status.supply_days_to_alert == 69.0


def test_resolve_filter_status_rejects_fractional_presentation_unit() -> None:
    """Test fractional units are not coerced to integers on either side."""
    supply_bad = _filter_edit_params()
    supply_bad["informationParams"]["61"] = [True, [[61.67, 2.5, 0]]]
    supply_status = resolve_filter_status(supply_bad)
    assert supply_status.supply_depletion is None
    assert supply_status.supply_days is None
    assert supply_status.supply_days_to_alert is None
    assert supply_status.extract_depletion == 61.67
    assert supply_status.extract_days == 111.0
    assert supply_status.extract_days_to_alert == 69.0

    extract_bad = _filter_edit_params()
    extract_bad["informationParams"]["62"] = [True, [[61.67, 2.5, 0]]]
    extract_bad["informationParams"]["64"] = [True, [[111, 13.5, 0]]]
    extract_status = resolve_filter_status(extract_bad)
    assert extract_status.extract_depletion is None
    assert extract_status.extract_days is None
    assert extract_status.extract_days_to_alert is None
    assert extract_status.supply_depletion == 61.67
    assert extract_status.supply_days == 111.0
    assert extract_status.supply_days_to_alert == 69.0


def test_resolve_filter_status_floors_days_to_alert_at_zero() -> None:
    """Test remaining days to alert is never negative past the threshold."""
    edit_params = _filter_edit_params()
    edit_params["data"]["574"]["value"] = 100
    edit_params["informationParams"]["61"] = [True, [[100.0, 2, 0]]]
    edit_params["informationParams"]["62"] = [True, [[100.0, 2, 0]]]
    edit_params["informationParams"]["63"] = [True, [[100, 13, 0]]]
    edit_params["informationParams"]["64"] = [True, [[120, 13, 0]]]
    # Extract days 120 with alarm 100 would not match depletion 100% — fix extract.
    edit_params["informationParams"]["62"] = [True, [[120.0, 2, 0]]]

    status = resolve_filter_status(edit_params)
    assert status.supply_days_to_alert == 0.0
    assert status.extract_days_to_alert == 0.0


async def test_filter_sensors_report_validated_slot_values(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test filter sensors report values from validated info slots and remaining days."""
    mock_api.async_get_edit_params.return_value = _filter_edit_params()
    await setup_integration(hass, mock_api)

    assert hass.states.get(SUPPLY_DEPL).state == "61.67"
    assert hass.states.get(EXTRACT_DEPL).state == "61.67"
    assert hass.states.get(SUPPLY_DAYS).state == "111.0"
    assert hass.states.get(EXTRACT_DAYS).state == "111.0"
    assert hass.states.get(SUPPLY_DAYS_TO_ALERT).state == "69.0"
    assert hass.states.get(EXTRACT_DAYS_TO_ALERT).state == "69.0"
    assert hass.states.get(SUPPLY_DEPL).attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert (
        hass.states.get(SUPPLY_DAYS).attributes[ATTR_UNIT_OF_MEASUREMENT]
        == UnitOfTime.DAYS
    )
    assert (
        hass.states.get(SUPPLY_DAYS_TO_ALERT).attributes[ATTR_UNIT_OF_MEASUREMENT]
        == UnitOfTime.DAYS
    )


async def test_filter_sensors_track_edit_params_refresh(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test filter sensors follow refreshed informationParams values."""
    mock_api.async_get_edit_params.return_value = _filter_edit_params()
    entry = await setup_integration(hass, mock_api)

    updated = deepcopy(_filter_edit_params())
    updated["informationParams"]["61"] = [True, [[70.0, 2, 0]]]
    updated["informationParams"]["62"] = [True, [[70.0, 2, 0]]]
    updated["informationParams"]["63"] = [True, [[140, 13, 0]]]
    updated["informationParams"]["64"] = [True, [[140, 13, 0]]]
    updated["data"]["574"]["value"] = 200
    mock_api.async_get_edit_params.return_value = updated

    await entry.runtime_data.async_request_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(SUPPLY_DEPL).state == "70.0"
    assert hass.states.get(EXTRACT_DEPL).state == "70.0"
    assert hass.states.get(SUPPLY_DAYS).state == "140.0"
    assert hass.states.get(EXTRACT_DAYS).state == "140.0"
    assert hass.states.get(SUPPLY_DAYS_TO_ALERT).state == "60.0"
    assert hass.states.get(EXTRACT_DAYS_TO_ALERT).state == "60.0"


async def test_filter_sensors_unavailable_without_valid_slots(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test filter sensors are unavailable when slots are missing or invalid."""
    await setup_integration(hass, mock_api)

    for entity_id in FILTER_ENTITIES:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_filter_sensors_unavailable_when_values_mismatch(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test mismatched depletion vs FILTERtimeToAlarm marks sensors unavailable."""
    edit_params = _filter_edit_params()
    edit_params["informationParams"]["61"] = [True, [[10.0, 2, 0]]]
    edit_params["informationParams"]["62"] = [True, [[10.0, 2, 0]]]
    mock_api.async_get_edit_params.return_value = edit_params
    await setup_integration(hass, mock_api)

    for entity_id in FILTER_ENTITIES:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_filter_sensor_unique_ids(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test filter sensors use stable unique IDs on the ecoNET device."""
    mock_api.async_get_edit_params.return_value = _filter_edit_params()
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    assert (
        registry.async_get(SUPPLY_DEPL).unique_id
        == f"{TEST_UID}_supply_air_filter_depletion"
    )
    assert (
        registry.async_get(EXTRACT_DEPL).unique_id
        == f"{TEST_UID}_extracted_air_filter_depletion"
    )
    assert (
        registry.async_get(SUPPLY_DAYS).unique_id
        == f"{TEST_UID}_supply_air_filter_operation_days"
    )
    assert (
        registry.async_get(EXTRACT_DAYS).unique_id
        == f"{TEST_UID}_extracted_air_filter_operation_days"
    )
    supply_alert = registry.async_get(SUPPLY_DAYS_TO_ALERT)
    extract_alert = registry.async_get(EXTRACT_DAYS_TO_ALERT)
    assert supply_alert is not None
    assert extract_alert is not None
    assert supply_alert.unique_id == f"{TEST_UID}_supply_air_filter_days_to_alert"
    assert extract_alert.unique_id == f"{TEST_UID}_extracted_air_filter_days_to_alert"
    assert supply_alert.entity_category is EntityCategory.DIAGNOSTIC
    assert extract_alert.entity_category is EntityCategory.DIAGNOSTIC
