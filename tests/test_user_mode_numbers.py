"""Tests for Plum ecoVENT User Mode fan and preset-temperature numbers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.number import ATTR_MODE, NumberMode
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.plum_ecovent.exceptions import PlumEconetConnectionError
from custom_components.plum_ecovent.models.user_mode import (
    USER_MODE_FAN_MAX,
    USER_MODE_FAN_MIN,
    USER_MODE_NUMBERS,
    USER_MODE_SETPOINT_MAX,
    USER_MODE_SETPOINT_MIN,
    resolve_user_mode_number,
)
from custom_components.plum_ecovent.parameters import resolve_writable_number_param
from tests.conftest import TEST_UID, setup_integration

MODE_1_SUPPLY = "number.plum_ecovent_mode_1_supply_fan_speed"
MODE_1_SETPOINT = "number.plum_ecovent_mode_1_target_temperature"
MODE_3_SETPOINT = "number.plum_ecovent_mode_3_target_temperature"
MODE_4_SUPPLY = "number.plum_ecovent_mode_4_supply_fan_speed"
MODE_4_SETPOINT = "number.plum_ecovent_mode_4_target_temperature"

ENTITY_BY_KEY = {
    spec.key: (
        f"number.plum_ecovent_{spec.key.removeprefix('user_').replace('preset_temperature', 'target_temperature')}"
    )
    for spec in USER_MODE_NUMBERS
}


def test_user_mode_specs_cover_all_twelve_params() -> None:
    """Test the User Mode table exposes twelve documented controls."""
    assert len(USER_MODE_NUMBERS) == 12
    ids = {spec.param_id for spec in USER_MODE_NUMBERS}
    assert ids == {
        273,
        274,
        275,
        276,
        277,
        278,
        286,
        287,
        288,
        468,
        469,
        470,
    }


def test_resolve_user_mode_prefers_curr(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test Modes 1–3 read the live value from regParams.curr."""
    spec = USER_MODE_NUMBERS[0]
    status = resolve_user_mode_number(reg_params, edit_params, spec)
    assert status.valid is True
    assert status.value == 40.0
    assert status.param_id == 273
    assert status.min_value == USER_MODE_FAN_MIN
    assert status.max_value == USER_MODE_FAN_MAX


def test_resolve_user_mode_falls_back_to_edit_params_value(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test Mode 4 (absent from curr) reads editParams.data value."""
    spec = next(s for s in USER_MODE_NUMBERS if s.param_id == 469)
    status = resolve_user_mode_number(reg_params, edit_params, spec)
    assert status.valid is True
    assert status.value == 70.0
    assert status.param_id == 469


def test_resolve_user_mode_rejects_id_mismatch(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test a wrong data key makes the number unavailable."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("273")
    edit_params["data"]["999"] = entry
    status = resolve_user_mode_number(reg_params, edit_params, USER_MODE_NUMBERS[0])
    assert status.valid is False


def test_resolve_user_mode_rejects_non_editable(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test edit:false makes the number unavailable."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["273"]["edit"] = False
    status = resolve_user_mode_number(reg_params, edit_params, USER_MODE_NUMBERS[0])
    assert status.valid is False


def test_resolve_user_mode_rejects_curr_numbers_mismatch(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test currNumbers disagreeing with the expected id is unavailable."""
    reg_params = deepcopy(reg_params)
    reg_params["currNumbers"]["REKUser1SupFanSpeed"] = 999
    status = resolve_user_mode_number(reg_params, edit_params, USER_MODE_NUMBERS[0])
    assert status.valid is False


def test_resolve_user_mode_rejects_non_numeric_value(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test non-numeric curr values are unavailable."""
    reg_params = deepcopy(reg_params)
    reg_params["curr"]["REKUser1SupFanSpeed"] = "fast"
    status = resolve_user_mode_number(reg_params, edit_params, USER_MODE_NUMBERS[0])
    assert status.valid is False


def test_resolve_uses_fallback_when_minv_maxv_degenerate(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test documented ranges apply when module advertises 0/0 bounds."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["273"]["minv"] = 0
    edit_params["data"]["273"]["maxv"] = 0
    status = resolve_writable_number_param(
        reg_params,
        edit_params,
        name="REKUser1SupFanSpeed",
        expected_id=273,
        fallback_min=USER_MODE_FAN_MIN,
        fallback_max=USER_MODE_FAN_MAX,
    )
    assert status.valid is True
    assert status.min_value == USER_MODE_FAN_MIN
    assert status.max_value == USER_MODE_FAN_MAX


async def test_user_mode_entities_expose_states_and_units(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test all twelve numbers come online with % or °C units."""
    await setup_integration(hass, mock_api)

    for spec in USER_MODE_NUMBERS:
        entity_id = ENTITY_BY_KEY[spec.key]
        state = hass.states.get(entity_id)
        assert state is not None, entity_id
        assert state.state != STATE_UNAVAILABLE
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == spec.unit
        assert state.attributes[ATTR_MODE] == NumberMode.SLIDER

    assert hass.states.get(MODE_1_SUPPLY).state == "40.0"
    assert hass.states.get(MODE_1_SETPOINT).state == "20.0"
    assert hass.states.get(MODE_4_SUPPLY).state == "70.0"
    assert hass.states.get(MODE_4_SETPOINT).state == "23.0"
    assert (
        hass.states.get(MODE_3_SETPOINT).attributes[ATTR_UNIT_OF_MEASUREMENT]
        == UnitOfTemperature.CELSIUS
    )
    assert (
        hass.states.get(MODE_1_SUPPLY).attributes[ATTR_UNIT_OF_MEASUREMENT]
        == PERCENTAGE
    )


async def test_user_mode_unique_ids(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test number unique ids are keyed by module uid and param key."""
    await setup_integration(hass, mock_api)
    registry = er.async_get(hass)

    for spec in USER_MODE_NUMBERS:
        entry = registry.async_get(ENTITY_BY_KEY[spec.key])
        assert entry is not None
        assert entry.unique_id == f"{TEST_UID}_{spec.key}"


async def test_user_mode_unavailable_on_id_mismatch(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test id mismatch marks the number unavailable and skips writes."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("273")
    edit_params["data"]["999"] = entry
    mock_api.async_get_edit_params.return_value = edit_params

    await setup_integration(hass, mock_api)

    state = hass.states.get(MODE_1_SUPPLY)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: MODE_1_SUPPLY, "value": 45},
        blocking=True,
    )
    mock_api.async_set_param.assert_not_awaited()


async def test_user_mode_write_uses_numeric_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test setting Mode 1 supply fan writes newParamName=273 and refreshes."""
    await setup_integration(hass, mock_api)

    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKUser1SupFanSpeed": 55},
    }

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: MODE_1_SUPPLY, "value": 55},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with("273", 55)
    assert hass.states.get(MODE_1_SUPPLY).state == "55.0"


async def test_user_mode_4_write_uses_edit_params_confirm(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test Mode 4 writes by id and confirms via refreshed editParams value."""
    await setup_integration(hass, mock_api)

    edit_params = deepcopy(edit_params)
    edit_params["data"]["469"]["value"] = 80
    mock_api.async_get_edit_params.return_value = edit_params

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: MODE_4_SUPPLY, "value": 80},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with("469", 80)
    assert hass.states.get(MODE_4_SUPPLY).state == "80.0"


async def test_user_mode_write_rejects_out_of_range(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test values outside module minv/maxv raise and do not write."""
    await setup_integration(hass, mock_api)

    with pytest.raises(HomeAssistantError, match="outside valid range"):
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: MODE_1_SUPPLY, "value": 10},
            blocking=True,
        )
    mock_api.async_set_param.assert_not_awaited()

    with pytest.raises(HomeAssistantError, match="outside valid range"):
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: MODE_1_SETPOINT, "value": 35},
            blocking=True,
        )
    mock_api.async_set_param.assert_not_awaited()


async def test_user_mode_write_failure_surfaces(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test newParam failures raise HomeAssistantError and keep state."""
    mock_api.async_set_param = AsyncMock(
        side_effect=PlumEconetConnectionError("Got 500")
    )
    await setup_integration(hass, mock_api)

    with pytest.raises(HomeAssistantError, match="Failed to set REKUser1SupFanSpeed"):
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: MODE_1_SUPPLY, "value": 45},
            blocking=True,
        )

    assert hass.states.get(MODE_1_SUPPLY).state == "40.0"


async def test_user_mode_setpoint_range_attributes(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test setpoint entities expose the documented °C range."""
    await setup_integration(hass, mock_api)

    state = hass.states.get(MODE_1_SETPOINT)
    assert state is not None
    assert state.attributes["min"] == USER_MODE_SETPOINT_MIN
    assert state.attributes["max"] == USER_MODE_SETPOINT_MAX

    fan = hass.states.get(MODE_1_SUPPLY)
    assert fan is not None
    assert fan.attributes["min"] == USER_MODE_FAN_MIN
    assert fan.attributes["max"] == USER_MODE_FAN_MAX
