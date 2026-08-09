"""Tests for Plum ecoVENT air-path temperature sensors."""

from typing import Any
from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    UnitOfTemperature,
)
from homeassistant.helpers import entity_registry as er

from tests.conftest import TEST_UID, setup_integration

SUPPLY_TEMP = "sensor.plum_ecovent_supply_air_temperature"
INTAKE_TEMP = "sensor.plum_ecovent_intake_air_temperature"
EXTRACTED_TEMP = "sensor.plum_ecovent_extracted_air_temperature"
EXHAUST_TEMP = "sensor.plum_ecovent_exhaust_air_temperature"

TEMP_ENTITIES = (SUPPLY_TEMP, INTAKE_TEMP, EXTRACTED_TEMP, EXHAUST_TEMP)


async def test_temperature_sensors_report_celsius_with_device_class(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test air-path temps report °C with temperature device class."""
    await setup_integration(hass, mock_api)

    expected = {
        SUPPLY_TEMP: "21.5",
        INTAKE_TEMP: "5.0",
        EXTRACTED_TEMP: "22.0",
        EXHAUST_TEMP: "18.5",
    }
    for entity_id, state in expected.items():
        entity = hass.states.get(entity_id)
        assert entity.state == state
        assert entity.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
        assert entity.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE


async def test_temperature_sensors_track_curr_updates(
    hass,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test temperature sensors follow coordinator refreshes of curr."""
    entry = await setup_integration(hass, mock_api)

    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {
            **reg_params["curr"],
            "REKcurSupTemp": 19.25,
            "REKcurIntTemp": -2.5,
            "REKcurExtTemp": 23.75,
            "REKcuExhTemp": 17.0,
        },
    }
    await entry.runtime_data.async_request_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(SUPPLY_TEMP).state == "19.25"
    assert hass.states.get(INTAKE_TEMP).state == "-2.5"
    assert hass.states.get(EXTRACTED_TEMP).state == "23.75"
    assert hass.states.get(EXHAUST_TEMP).state == "17.0"


async def test_temperature_sensors_unavailable_when_curr_key_missing(
    hass,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test missing curr keys mark temperature sensors unavailable."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {
            "REKcurSupFanSpeed": 10,
            "REKcurExhFanSpeed": 12,
        },
    }
    await setup_integration(hass, mock_api)

    for entity_id in TEMP_ENTITIES:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_temperature_sensors_unavailable_for_nonnumeric_curr_values(
    hass,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test nonnumeric curr values mark temperature sensors unavailable."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {
            **reg_params["curr"],
            "REKcurSupTemp": "not-a-number",
            "REKcurIntTemp": None,
            "REKcurExtTemp": "",
            "REKcuExhTemp": {"v": 1},
        },
    }
    await setup_integration(hass, mock_api)

    for entity_id in TEMP_ENTITIES:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_temperature_sensors_unavailable_for_nonfinite_curr_values(
    hass,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test NaN/Infinity curr values mark temperature sensors unavailable."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {
            **reg_params["curr"],
            "REKcurSupTemp": "NaN",
            "REKcurIntTemp": "Infinity",
            "REKcurExtTemp": "-Infinity",
            "REKcuExhTemp": float("nan"),
        },
    }
    await setup_integration(hass, mock_api)

    for entity_id in TEMP_ENTITIES:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_temperature_sensors_handle_malformed_curr_container(
    hass,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test a malformed nested curr payload does not break entity updates."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": ["not", "a", "mapping"],
    }
    await setup_integration(hass, mock_api)

    for entity_id in TEMP_ENTITIES:
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_temperature_sensor_unique_ids(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test temperature sensors use stable unique IDs on the ecoNET device."""
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    assert (
        registry.async_get(SUPPLY_TEMP).unique_id
        == f"{TEST_UID}_supply_air_temperature"
    )
    assert (
        registry.async_get(INTAKE_TEMP).unique_id
        == f"{TEST_UID}_intake_air_temperature"
    )
    assert (
        registry.async_get(EXTRACTED_TEMP).unique_id
        == f"{TEST_UID}_extracted_air_temperature"
    )
    assert (
        registry.async_get(EXHAUST_TEMP).unique_id
        == f"{TEST_UID}_exhaust_air_temperature"
    )
