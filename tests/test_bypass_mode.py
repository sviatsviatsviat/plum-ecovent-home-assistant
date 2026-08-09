"""Tests for Plum ecoVENT bypass mode select and companion sensors."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_OPTION,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.plum_ecovent.exceptions import PlumEconetConnectionError
from custom_components.plum_ecovent.models.bypass import (
    BYPASS_MODES,
    OPTION_UNSUPPORTED,
    BypassMode,
    BypassMotorState,
    resolve_bypass_mode,
    resolve_bypass_motor_state_option,
)
from tests.conftest import TEST_UID, setup_integration

BYPASS_MODE = "select.plum_ecovent_bypass_mode"
BYPASS_MOTOR = "sensor.plum_ecovent_bypass_motor_state"
BYPASS_OPEN = "sensor.plum_ecovent_bypass_open_level"

WIRE_CASES = (
    *((mode.value, mode.option) for mode in BYPASS_MODES),
    (257, OPTION_UNSUPPORTED),
    (0, OPTION_UNSUPPORTED),
    (1, OPTION_UNSUPPORTED),
)


def test_bypass_mode_enum_wires() -> None:
    """Test BypassMode encapsulates packed wire values and option keys."""
    assert BypassMode.CLOSE == 265
    assert BypassMode.OPEN == 273
    assert BypassMode.AUTO == 289
    assert BypassMode.AUTO.option == "auto"
    assert BypassMode.OPEN.option == "open"
    assert BypassMode.CLOSE.option == "close"
    assert BypassMode.from_wire(289) is BypassMode.AUTO
    assert BypassMode.from_wire(257) is None
    assert BypassMode.from_option("open") is BypassMode.OPEN
    assert BypassMode.from_option("273") is None
    assert [mode.option for mode in BYPASS_MODES] == ["auto", "open", "close"]


def test_resolve_bypass_mode_accepts_expected_id(
    edit_params: dict[str, Any],
) -> None:
    """Test BYPmodSett resolves when name maps to id 342 and is editable."""
    status = resolve_bypass_mode(edit_params)
    assert status.valid is True
    assert status.wire == BypassMode.AUTO
    assert status.mode is BypassMode.AUTO
    assert status.option == BypassMode.AUTO.option


def test_resolve_bypass_mode_rejects_id_mismatch(
    edit_params: dict[str, Any],
) -> None:
    """Test a wrong data key for BYPmodSett makes the entity unavailable."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("342")
    edit_params["data"]["99"] = entry

    status = resolve_bypass_mode(edit_params)
    assert status.valid is False
    assert status.option is None
    assert status.mode is None


def test_resolve_bypass_mode_rejects_missing_name(
    edit_params: dict[str, Any],
) -> None:
    """Test missing BYPmodSett in editParams.data is unavailable."""
    edit_params = deepcopy(edit_params)
    del edit_params["data"]["342"]

    status = resolve_bypass_mode(edit_params)
    assert status.valid is False


def test_resolve_bypass_mode_rejects_non_editable(
    edit_params: dict[str, Any],
) -> None:
    """Test edit:false BYPmodSett is unavailable."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["342"]["edit"] = False

    status = resolve_bypass_mode(edit_params)
    assert status.valid is False


def test_resolve_bypass_mode_rejects_non_integer_value(
    edit_params: dict[str, Any],
) -> None:
    """Test a non-integer editParams value is unavailable."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["342"]["value"] = 2.5

    status = resolve_bypass_mode(edit_params)
    assert status.valid is False


@pytest.mark.parametrize(("wire", "option"), WIRE_CASES)
async def test_bypass_mode_maps_wire_values(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
    wire: int,
    option: str,
) -> None:
    """Test Auto/Open/Close wire options and Unsupported for other values."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["342"]["value"] = wire
    mock_api.async_get_edit_params.return_value = edit_params
    await setup_integration(hass, mock_api)

    state = hass.states.get(BYPASS_MODE)
    assert state is not None
    assert state.state == option
    assert BypassMode.AUTO.option in state.attributes["options"]
    assert BypassMode.CLOSE.option in state.attributes["options"]
    if option == OPTION_UNSUPPORTED:
        assert OPTION_UNSUPPORTED in state.attributes["options"]
    else:
        assert OPTION_UNSUPPORTED not in state.attributes["options"]


async def test_bypass_mode_unique_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test the select unique id is keyed by module uid."""
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    entry = registry.async_get(BYPASS_MODE)
    assert entry is not None
    assert entry.unique_id == f"{TEST_UID}_bypass_mode"
    assert entry.entity_category is EntityCategory.CONFIG


async def test_bypass_mode_unavailable_on_id_mismatch(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test id mismatch marks the select unavailable and skips writes."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("342")
    edit_params["data"]["99"] = entry
    mock_api.async_get_edit_params.return_value = edit_params

    await setup_integration(hass, mock_api)

    state = hass.states.get(BYPASS_MODE)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: BYPASS_MODE,
            ATTR_OPTION: BypassMode.OPEN.option,
        },
        blocking=True,
    )
    mock_api.async_set_param.assert_not_awaited()


async def test_bypass_mode_write_uses_numeric_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test selecting Open writes newParamName=342 and refreshes editParams."""
    await setup_integration(hass, mock_api)

    edit_params = deepcopy(edit_params)
    edit_params["data"]["342"]["value"] = BypassMode.OPEN
    mock_api.async_get_edit_params.return_value = edit_params

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: BYPASS_MODE,
            ATTR_OPTION: BypassMode.OPEN.option,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with(
        "342", BypassMode.OPEN.value
    )
    assert hass.states.get(BYPASS_MODE).state == BypassMode.OPEN.option


@pytest.mark.parametrize("mode", list(BYPASS_MODES))
async def test_bypass_mode_write_all_writable_options(
    hass: HomeAssistant,
    mock_api: MagicMock,
    mode: BypassMode,
) -> None:
    """Test each writable mode sends its full packed wire value."""
    await setup_integration(hass, mock_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {ATTR_ENTITY_ID: BYPASS_MODE, ATTR_OPTION: mode.option},
        blocking=True,
    )

    mock_api.async_set_param.assert_awaited_once_with("342", mode.value)


async def test_bypass_mode_write_failure_surfaces(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test newParam failures raise HomeAssistantError and keep state."""
    mock_api.async_set_param = AsyncMock(
        side_effect=PlumEconetConnectionError("Got 500")
    )
    await setup_integration(hass, mock_api)

    with pytest.raises(HomeAssistantError, match="Failed to set bypass mode"):
        await hass.services.async_call(
            "select",
            "select_option",
            {
                ATTR_ENTITY_ID: BYPASS_MODE,
                ATTR_OPTION: BypassMode.CLOSE.option,
            },
            blocking=True,
        )

    assert hass.states.get(BYPASS_MODE).state == BypassMode.AUTO.option


async def test_bypass_mode_rejects_selecting_unknown(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test Unsupported is display-only and cannot be written."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["342"]["value"] = 257
    mock_api.async_get_edit_params.return_value = edit_params
    await setup_integration(hass, mock_api)

    assert hass.states.get(BYPASS_MODE).state == OPTION_UNSUPPORTED

    with pytest.raises(HomeAssistantError, match="read-only"):
        await hass.services.async_call(
            "select",
            "select_option",
            {ATTR_ENTITY_ID: BYPASS_MODE, ATTR_OPTION: OPTION_UNSUPPORTED},
            blocking=True,
        )
    mock_api.async_set_param.assert_not_awaited()


def test_resolve_bypass_motor_state_option(
    reg_params: dict[str, Any],
) -> None:
    """Test BYPmodState maps Off/On and Unsupported."""
    assert resolve_bypass_motor_state_option(reg_params) == BypassMotorState.OFF.option

    reg = deepcopy(reg_params)
    reg["curr"]["BYPmodState"] = 1
    assert resolve_bypass_motor_state_option(reg) == BypassMotorState.ON.option

    reg["curr"]["BYPmodState"] = 2
    assert resolve_bypass_motor_state_option(reg) == OPTION_UNSUPPORTED

    del reg["curr"]["BYPmodState"]
    assert resolve_bypass_motor_state_option(reg) is None


async def test_bypass_companion_sensors(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test motor state and open level companions follow regParams.curr."""
    entry = await setup_integration(hass, mock_api)

    motor = hass.states.get(BYPASS_MOTOR)
    open_level = hass.states.get(BYPASS_OPEN)
    assert motor is not None
    assert open_level is not None
    assert motor.state == BypassMotorState.OFF.option
    assert open_level.state == "0.0"
    assert open_level.attributes["unit_of_measurement"] == PERCENTAGE
    assert open_level.attributes["icon"] == "mdi:valve-closed"

    registry = er.async_get(hass)
    assert registry.async_get(BYPASS_MOTOR).unique_id == f"{TEST_UID}_bypass_motor_state"
    assert registry.async_get(BYPASS_OPEN).unique_id == f"{TEST_UID}_bypass_open_level"

    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {
            **reg_params["curr"],
            "BYPmodState": 1,
            "BYPcurControl": 100.0,
        },
    }
    await entry.runtime_data.async_request_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(BYPASS_MOTOR).state == BypassMotorState.ON.option
    open_full = hass.states.get(BYPASS_OPEN)
    assert open_full is not None
    assert open_full.state == "100.0"
    assert open_full.attributes["icon"] == "mdi:valve-open"


async def test_bypass_open_level_partial_uses_valve_icon(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test intermediate open levels use mdi:valve."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {
            **reg_params["curr"],
            "BYPcurControl": 45.0,
        },
    }
    await setup_integration(hass, mock_api)

    open_mid = hass.states.get(BYPASS_OPEN)
    assert open_mid is not None
    assert open_mid.state == "45.0"
    assert open_mid.attributes["icon"] == "mdi:valve"


async def test_bypass_companion_sensors_unavailable_when_curr_missing(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test missing curr keys mark companion sensors unavailable."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {"REKWS1": 6},
    }
    await setup_integration(hass, mock_api)

    assert hass.states.get(BYPASS_MOTOR).state == STATE_UNAVAILABLE
    assert hass.states.get(BYPASS_OPEN).state == STATE_UNAVAILABLE
