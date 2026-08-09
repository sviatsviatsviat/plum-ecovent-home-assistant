"""Tests for Plum ecoVENT fan speed sensors."""

from typing import Any
from unittest.mock import MagicMock

from homeassistant.const import PERCENTAGE, STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry as er

from tests.conftest import TEST_UID, setup_integration

SUPPLY_SPEED = "sensor.plum_ecovent_supply_fan_speed"
EXHAUST_SPEED = "sensor.plum_ecovent_exhaust_fan_speed"


async def test_fan_speed_sensors_report_zero_with_fan_off_icon(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test zero fan speeds report 0% with mdi:fan-off."""
    await setup_integration(hass, mock_api)

    supply = hass.states.get(SUPPLY_SPEED)
    exhaust = hass.states.get(EXHAUST_SPEED)
    assert supply.state == "0.0"
    assert exhaust.state == "0.0"
    assert supply.attributes["unit_of_measurement"] == PERCENTAGE
    assert exhaust.attributes["unit_of_measurement"] == PERCENTAGE
    assert supply.attributes["icon"] == "mdi:fan-off"
    assert exhaust.attributes["icon"] == "mdi:fan-off"


async def test_fan_speed_sensors_track_nonzero_with_fan_icon(
    hass,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test non-zero speeds follow coordinator refresh and use mdi:fan."""
    entry = await setup_integration(hass, mock_api)

    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {
            **reg_params["curr"],
            "REKcurSupFanSpeed": 35,
            "REKcurExhFanSpeed": 40,
        },
    }
    await entry.runtime_data.async_request_refresh()
    await hass.async_block_till_done()

    supply = hass.states.get(SUPPLY_SPEED)
    exhaust = hass.states.get(EXHAUST_SPEED)
    assert supply.state == "35.0"
    assert exhaust.state == "40.0"
    assert supply.attributes["icon"] == "mdi:fan"
    assert exhaust.attributes["icon"] == "mdi:fan"


async def test_fan_speed_sensors_unavailable_when_curr_key_missing(
    hass,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test missing curr keys mark the fan speed sensors unavailable."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {"REKcurSupTemp": 21.5},
    }
    await setup_integration(hass, mock_api)

    assert hass.states.get(SUPPLY_SPEED).state == STATE_UNAVAILABLE
    assert hass.states.get(EXHAUST_SPEED).state == STATE_UNAVAILABLE


async def test_fan_speed_sensor_unique_ids(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test fan speed sensors use stable unique IDs on the ecoNET device."""
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    assert (
        registry.async_get(SUPPLY_SPEED).unique_id == f"{TEST_UID}_supply_fan_speed"
    )
    assert (
        registry.async_get(EXHAUST_SPEED).unique_id == f"{TEST_UID}_exhaust_fan_speed"
    )
