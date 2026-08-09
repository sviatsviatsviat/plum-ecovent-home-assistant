"""Tests for Plum ecoVENT recuperation operation mode select."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import ATTR_ENTITY_ID, ATTR_OPTION, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.plum_ecovent.exceptions import PlumEconetConnectionError
from custom_components.plum_ecovent.models.operation import (
    OPERATION_MODES,
    OPTION_UNSUPPORTED,
    OperationMode,
    resolve_operation_mode,
)
from tests.conftest import TEST_UID, setup_integration

OPERATION_MODE = "select.plum_ecovent_recuperation_operation_mode"

WIRE_CASES = (
    *((mode.value, mode.option) for mode in OPERATION_MODES),
    (0, OPTION_UNSUPPORTED),
    (1, OPTION_UNSUPPORTED),
    (2, OPTION_UNSUPPORTED),
    (8, OPTION_UNSUPPORTED),
)


def test_operation_mode_enum_wires() -> None:
    """Test OperationMode encapsulates wire values and option keys."""
    assert OperationMode.MODE_1 == 3
    assert OperationMode.MODE_2 == 4
    assert OperationMode.MODE_3 == 5
    assert OperationMode.HALT == 6
    assert OperationMode.MODE_4 == 7
    assert OperationMode.HALT.option == "halt"
    assert OperationMode.MODE_1.option == "mode_1"
    assert OperationMode.from_wire(6) is OperationMode.HALT
    assert OperationMode.from_wire(0) is None
    assert OperationMode.from_option("mode_1") is OperationMode.MODE_1
    assert OperationMode.from_option("3") is None
    assert [mode.option for mode in OPERATION_MODES] == [
        "halt",
        "mode_1",
        "mode_2",
        "mode_3",
        "mode_4",
    ]


def test_resolve_operation_mode_accepts_expected_id(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test REKWS1 resolves when name maps to id 17 and is editable."""
    status = resolve_operation_mode(reg_params, edit_params)
    assert status.valid is True
    assert status.wire == OperationMode.HALT
    assert status.mode is OperationMode.HALT
    assert status.option == OperationMode.HALT.option


def test_resolve_operation_mode_rejects_id_mismatch(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test a wrong data key for REKWS1 makes the entity unavailable."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("17")
    edit_params["data"]["99"] = entry

    status = resolve_operation_mode(reg_params, edit_params)
    assert status.valid is False
    assert status.option is None
    assert status.mode is None


def test_resolve_operation_mode_rejects_missing_name(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test missing REKWS1 in editParams.data is unavailable."""
    edit_params = deepcopy(edit_params)
    del edit_params["data"]["17"]

    status = resolve_operation_mode(reg_params, edit_params)
    assert status.valid is False


def test_resolve_operation_mode_rejects_non_editable(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test edit:false REKWS1 is unavailable."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["17"]["edit"] = False

    status = resolve_operation_mode(reg_params, edit_params)
    assert status.valid is False


def test_resolve_operation_mode_rejects_curr_numbers_mismatch(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test currNumbers disagreeing with id 17 is unavailable."""
    reg_params = deepcopy(reg_params)
    reg_params["currNumbers"]["REKWS1"] = 99

    status = resolve_operation_mode(reg_params, edit_params)
    assert status.valid is False


@pytest.mark.parametrize(("wire", "option"), WIRE_CASES)
async def test_operation_mode_maps_wire_values(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
    wire: int,
    option: str,
) -> None:
    """Test Halt/Mode 1–4 wire options and Unsupported for other values."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKWS1": wire},
    }
    await setup_integration(hass, mock_api)

    state = hass.states.get(OPERATION_MODE)
    assert state is not None
    assert state.state == option
    assert OperationMode.HALT.option in state.attributes["options"]
    assert OperationMode.MODE_1.option in state.attributes["options"]
    if option == OPTION_UNSUPPORTED:
        assert OPTION_UNSUPPORTED in state.attributes["options"]
    else:
        assert OPTION_UNSUPPORTED not in state.attributes["options"]


async def test_operation_mode_unique_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test the select unique id is keyed by module uid."""
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    entry = registry.async_get(OPERATION_MODE)
    assert entry is not None
    assert entry.unique_id == f"{TEST_UID}_operation_mode"


async def test_operation_mode_unavailable_on_id_mismatch(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test id mismatch marks the select unavailable and skips writes."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("17")
    edit_params["data"]["99"] = entry
    mock_api.async_get_edit_params.return_value = edit_params

    await setup_integration(hass, mock_api)

    state = hass.states.get(OPERATION_MODE)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Home Assistant skips service calls on unavailable entities.
    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: OPERATION_MODE,
            ATTR_OPTION: OperationMode.MODE_1.option,
        },
        blocking=True,
    )
    mock_api.async_set_param.assert_not_awaited()


async def test_operation_mode_write_uses_numeric_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test selecting Mode 1 writes newParamName=17 and refreshes curr."""
    await setup_integration(hass, mock_api)

    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKWS1": OperationMode.MODE_1},
    }

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: OPERATION_MODE,
            ATTR_OPTION: OperationMode.MODE_1.option,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with(
        "17", OperationMode.MODE_1.value
    )
    assert hass.states.get(OPERATION_MODE).state == OperationMode.MODE_1.option


@pytest.mark.parametrize("mode", list(OPERATION_MODES))
async def test_operation_mode_write_all_writable_options(
    hass: HomeAssistant,
    mock_api: MagicMock,
    mode: OperationMode,
) -> None:
    """Test each writable mode sends its wire value."""
    await setup_integration(hass, mock_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {ATTR_ENTITY_ID: OPERATION_MODE, ATTR_OPTION: mode.option},
        blocking=True,
    )

    mock_api.async_set_param.assert_awaited_once_with("17", mode.value)


async def test_operation_mode_write_failure_surfaces(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test newParam failures raise HomeAssistantError and keep state."""
    mock_api.async_set_param = AsyncMock(
        side_effect=PlumEconetConnectionError("Got 500")
    )
    await setup_integration(hass, mock_api)

    with pytest.raises(HomeAssistantError, match="Failed to set operation mode"):
        await hass.services.async_call(
            "select",
            "select_option",
            {
                ATTR_ENTITY_ID: OPERATION_MODE,
                ATTR_OPTION: OperationMode.MODE_2.option,
            },
            blocking=True,
        )

    assert hass.states.get(OPERATION_MODE).state == OperationMode.HALT.option


async def test_operation_mode_rejects_selecting_unknown(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test Unsupported is display-only and cannot be written."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKWS1": 0},
    }
    await setup_integration(hass, mock_api)

    assert hass.states.get(OPERATION_MODE).state == OPTION_UNSUPPORTED

    with pytest.raises(HomeAssistantError, match="read-only"):
        await hass.services.async_call(
            "select",
            "select_option",
            {ATTR_ENTITY_ID: OPERATION_MODE, ATTR_OPTION: OPTION_UNSUPPORTED},
            blocking=True,
        )
    mock_api.async_set_param.assert_not_awaited()
