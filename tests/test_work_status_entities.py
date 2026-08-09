"""Tests for Plum ecoVENT Current work status sensors (slots 101–105)."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.helpers import entity_registry as er

from custom_components.plum_ecovent.models.work import resolve_work_status
from tests.conftest import TEST_UID, setup_integration

COMFORT = "sensor.plum_ecovent_current_comfort_temperature"
LEADING = "sensor.plum_ecovent_current_leading_temperature"
CONTROL = "sensor.plum_ecovent_control_mode"
EXTERNAL = "sensor.plum_ecovent_external_temperature"
SEASON = "sensor.plum_ecovent_summer_winter"
WORK_STATUS_ENTITIES = (COMFORT, LEADING, CONTROL, EXTERNAL, SEASON)


def _work_status_edit_params() -> dict[str, Any]:
    """editParams fixture with Current work status slots 101–105."""
    return {
        "editableParamsVer": 50,
        "data": {
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
            "101": [True, [[20, 1, 0]]],
            "102": [True, [["25.6", 1, 0]]],
            "103": [True, [["0", 0, 1]]],
            "104": [True, [["21.5", 1, 0]]],
            "105": [True, [["2", 0, 1]]],
            # Peer noise — ignored (bypass / Wi‑Fi / filter).
            "91": [True, [["0", 0, 1]]],
            "61": [True, [[61.67, 2, 0]]],
            "234": [True, [[60, 2, 0]]],
        },
    }


def test_resolve_work_status_reads_slots_101_to_105() -> None:
    """Test fixed slots 101–105 parse temperatures and mode wires."""
    status = resolve_work_status(_work_status_edit_params())
    assert status.comfort_temperature == 20.0
    assert status.leading_temperature == 25.6
    assert status.control_mode_wire == 0
    assert status.control_mode_option == "heating"
    assert status.external_temperature == 21.5
    assert status.season_status_wire == 2
    assert status.season_status_option == "auto_summer"


def test_resolve_work_status_maps_control_and_season_wires() -> None:
    """Test Heating/Cooling and Summer/Winter wire maps including Auto—Winter."""
    edit_params = _work_status_edit_params()
    edit_params["informationParams"]["103"] = [True, [["1", 0, 1]]]
    edit_params["informationParams"]["105"] = [True, [["3", 0, 1]]]
    status = resolve_work_status(edit_params)
    assert status.control_mode_option == "cooling"
    assert status.season_status_option == "auto_winter"

    edit_params["informationParams"]["105"] = [True, [[4, 0, 1]]]
    assert resolve_work_status(edit_params).season_status_option == "ventilation"
    edit_params["informationParams"]["105"] = [True, [["0", 0, 1]]]
    assert resolve_work_status(edit_params).season_status_option == "summer"
    edit_params["informationParams"]["105"] = [True, [["1", 0, 1]]]
    assert resolve_work_status(edit_params).season_status_option == "winter"


def test_resolve_work_status_marks_unexpected_wires_unsupported() -> None:
    """Test unmapped mode wires become Unsupported rather than unavailable."""
    edit_params = _work_status_edit_params()
    edit_params["informationParams"]["103"] = [True, [["9", 0, 1]]]
    edit_params["informationParams"]["105"] = [True, [["99", 0, 1]]]
    status = resolve_work_status(edit_params)
    assert status.control_mode_wire == 9
    assert status.control_mode_option == "unsupported"
    assert status.season_status_wire == 99
    assert status.season_status_option == "unsupported"


def test_resolve_work_status_rejects_wrong_units_and_missing_slots() -> None:
    """Test wrong presentation units or missing slots yield None fields."""
    edit_params = _work_status_edit_params()
    edit_params["informationParams"]["101"] = [True, [[20, 2, 0]]]
    edit_params["informationParams"]["103"] = [True, [["0", 1, 0]]]
    del edit_params["informationParams"]["104"]
    status = resolve_work_status(edit_params)
    assert status.comfort_temperature is None
    assert status.control_mode_wire is None
    assert status.external_temperature is None
    assert status.leading_temperature == 25.6


def test_resolve_work_status_rejects_non_finite_temperatures() -> None:
    """Test nan/inf temperature slots are rejected."""
    edit_params = _work_status_edit_params()
    edit_params["informationParams"]["101"] = [True, [[math.nan, 1, 0]]]
    edit_params["informationParams"]["102"] = [True, [[math.inf, 1, 0]]]
    status = resolve_work_status(edit_params)
    assert status.comfort_temperature is None
    assert status.leading_temperature is None


def test_resolve_work_status_rejects_boolean_temperatures() -> None:
    """Test bool temperature values are rejected (float(True)==1.0)."""
    edit_params = _work_status_edit_params()
    edit_params["informationParams"]["101"] = [True, [[True, 1, 0]]]
    edit_params["informationParams"]["102"] = [True, [[False, 1, 0]]]
    status = resolve_work_status(edit_params)
    assert status.comfort_temperature is None
    assert status.leading_temperature is None


async def test_work_status_sensors_report_diagnostic_values(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test five diagnostic sensors report values from slots 101–105."""
    mock_api.async_get_edit_params.return_value = _work_status_edit_params()
    await setup_integration(hass, mock_api)

    assert hass.states.get(COMFORT).state == "20.0"
    assert hass.states.get(LEADING).state == "25.6"
    assert hass.states.get(CONTROL).state == "heating"
    assert hass.states.get(EXTERNAL).state == "21.5"
    assert hass.states.get(SEASON).state == "auto_summer"

    for entity_id in (COMFORT, LEADING, EXTERNAL):
        state = hass.states.get(entity_id)
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
        assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE

    for entity_id in (CONTROL, SEASON):
        state = hass.states.get(entity_id)
        assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM

    registry = er.async_get(hass)
    for entity_id in WORK_STATUS_ENTITIES:
        assert registry.async_get(entity_id).entity_category == EntityCategory.DIAGNOSTIC


async def test_work_status_sensors_track_edit_params_refresh(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test work status sensors follow refreshed informationParams values."""
    mock_api.async_get_edit_params.return_value = _work_status_edit_params()
    entry = await setup_integration(hass, mock_api)

    updated = deepcopy(_work_status_edit_params())
    updated["informationParams"]["101"] = [True, [[30, 1, 0]]]
    updated["informationParams"]["102"] = [True, [["24.0", 1, 0]]]
    updated["informationParams"]["103"] = [True, [["1", 0, 1]]]
    updated["informationParams"]["104"] = [True, [["19.25", 1, 0]]]
    updated["informationParams"]["105"] = [True, [["4", 0, 1]]]
    mock_api.async_get_edit_params.return_value = updated

    await entry.runtime_data.async_request_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(COMFORT).state == "30.0"
    assert hass.states.get(LEADING).state == "24.0"
    assert hass.states.get(CONTROL).state == "cooling"
    assert hass.states.get(EXTERNAL).state == "19.25"
    assert hass.states.get(SEASON).state == "ventilation"


async def test_work_status_sensors_unavailable_without_slots(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test work status sensors are unavailable when slots are missing."""
    await setup_integration(hass, mock_api)

    for entity_id in WORK_STATUS_ENTITIES:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_work_status_enum_sensors_report_unsupported_wires(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test unexpected mode wires surface as Unsupported."""
    edit_params = _work_status_edit_params()
    edit_params["informationParams"]["103"] = [True, [["7", 0, 1]]]
    edit_params["informationParams"]["105"] = [True, [["8", 0, 1]]]
    mock_api.async_get_edit_params.return_value = edit_params
    await setup_integration(hass, mock_api)

    assert hass.states.get(CONTROL).state == "unsupported"
    assert hass.states.get(SEASON).state == "unsupported"


async def test_work_status_sensor_unique_ids_and_category(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test work status sensors use stable unique IDs and diagnostic category."""
    mock_api.async_get_edit_params.return_value = _work_status_edit_params()
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    expected = {
        COMFORT: f"{TEST_UID}_current_comfort_temperature",
        LEADING: f"{TEST_UID}_current_leading_temperature",
        CONTROL: f"{TEST_UID}_control_mode",
        EXTERNAL: f"{TEST_UID}_external_temperature",
        SEASON: f"{TEST_UID}_summer_winter_status",
    }
    for entity_id, unique_id in expected.items():
        entry = registry.async_get(entity_id)
        assert entry is not None
        assert entry.unique_id == unique_id
        assert entry.entity_category == EntityCategory.DIAGNOSTIC
