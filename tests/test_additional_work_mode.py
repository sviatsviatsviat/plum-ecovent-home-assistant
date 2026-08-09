"""Tests for Plum ecoVENT additional / timed work mode select."""

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
from custom_components.plum_ecovent.models.additional_work import (
    ADDITIONAL_WORK_MODES,
    OPTION_UNSUPPORTED,
    AdditionalWorkMode,
    resolve_additional_work_mode,
)
from tests.conftest import TEST_UID, setup_integration

ADDITIONAL_WORK_MODE = "select.plum_ecovent_additional_work_mode"

WIRE_CASES = (
    *((mode.value, mode.option) for mode in ADDITIONAL_WORK_MODES),
    (3, OPTION_UNSUPPORTED),
    (5, OPTION_UNSUPPORTED),
    (8, OPTION_UNSUPPORTED),
)


def test_additional_work_mode_enum_wires() -> None:
    """Test AdditionalWorkMode encapsulates wire values and option keys."""
    assert AdditionalWorkMode.OFF == 0
    assert AdditionalWorkMode.OUTSIDE == 1
    assert AdditionalWorkMode.PARTY == 2
    assert AdditionalWorkMode.AIRING == 4
    assert AdditionalWorkMode.OFF.option == "off"
    assert AdditionalWorkMode.AIRING.option == "airing"
    assert AdditionalWorkMode.from_wire(2) is AdditionalWorkMode.PARTY
    assert AdditionalWorkMode.from_wire(3) is None
    assert AdditionalWorkMode.from_option("party") is AdditionalWorkMode.PARTY
    assert AdditionalWorkMode.from_option("3") is None
    assert [mode.option for mode in ADDITIONAL_WORK_MODES] == [
        "off",
        "outside",
        "party",
        "airing",
    ]


def test_resolve_additional_work_mode_accepts_expected_id(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test REKWS4 resolves when name maps to id 20 and is editable."""
    status = resolve_additional_work_mode(reg_params, edit_params)
    assert status.valid is True
    assert status.wire == AdditionalWorkMode.OFF
    assert status.mode is AdditionalWorkMode.OFF
    assert status.option == AdditionalWorkMode.OFF.option


def test_resolve_additional_work_mode_rejects_id_mismatch(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test a wrong data key for REKWS4 makes the entity unavailable."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("20")
    edit_params["data"]["99"] = entry

    status = resolve_additional_work_mode(reg_params, edit_params)
    assert status.valid is False
    assert status.option is None
    assert status.mode is None


def test_resolve_additional_work_mode_rejects_missing_name(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test missing REKWS4 in editParams.data is unavailable."""
    edit_params = deepcopy(edit_params)
    del edit_params["data"]["20"]

    status = resolve_additional_work_mode(reg_params, edit_params)
    assert status.valid is False


def test_resolve_additional_work_mode_rejects_non_editable(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test edit:false REKWS4 is unavailable."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["20"]["edit"] = False

    status = resolve_additional_work_mode(reg_params, edit_params)
    assert status.valid is False


def test_resolve_additional_work_mode_rejects_curr_numbers_mismatch(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test currNumbers disagreeing with id 20 is unavailable."""
    reg_params = deepcopy(reg_params)
    reg_params["currNumbers"]["REKWS4"] = 99

    status = resolve_additional_work_mode(reg_params, edit_params)
    assert status.valid is False


@pytest.mark.parametrize(("wire", "option"), WIRE_CASES)
async def test_additional_work_mode_maps_wire_values(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
    wire: int,
    option: str,
) -> None:
    """Test Off/Outside/Party/Airing wire options and Unsupported for other values."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKWS4": wire},
    }
    await setup_integration(hass, mock_api)

    state = hass.states.get(ADDITIONAL_WORK_MODE)
    assert state is not None
    assert state.state == option
    assert AdditionalWorkMode.OFF.option in state.attributes["options"]
    assert AdditionalWorkMode.AIRING.option in state.attributes["options"]
    if option == OPTION_UNSUPPORTED:
        assert OPTION_UNSUPPORTED in state.attributes["options"]
    else:
        assert OPTION_UNSUPPORTED not in state.attributes["options"]


async def test_additional_work_mode_unique_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test the select unique id is keyed by module uid."""
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    entry = registry.async_get(ADDITIONAL_WORK_MODE)
    assert entry is not None
    assert entry.unique_id == f"{TEST_UID}_additional_work_mode"


async def test_additional_work_mode_unavailable_on_id_mismatch(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test id mismatch marks the select unavailable and skips writes."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("20")
    edit_params["data"]["99"] = entry
    mock_api.async_get_edit_params.return_value = edit_params

    await setup_integration(hass, mock_api)

    state = hass.states.get(ADDITIONAL_WORK_MODE)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Home Assistant skips service calls on unavailable entities.
    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: ADDITIONAL_WORK_MODE,
            ATTR_OPTION: AdditionalWorkMode.PARTY.option,
        },
        blocking=True,
    )
    mock_api.async_set_param.assert_not_awaited()


async def test_additional_work_mode_write_uses_numeric_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test selecting Party writes newParamName=20 and refreshes curr."""
    await setup_integration(hass, mock_api)

    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKWS4": AdditionalWorkMode.PARTY},
    }

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: ADDITIONAL_WORK_MODE,
            ATTR_OPTION: AdditionalWorkMode.PARTY.option,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with(
        "20", AdditionalWorkMode.PARTY.value
    )
    assert (
        hass.states.get(ADDITIONAL_WORK_MODE).state == AdditionalWorkMode.PARTY.option
    )


@pytest.mark.parametrize("mode", list(ADDITIONAL_WORK_MODES))
async def test_additional_work_mode_write_all_writable_options(
    hass: HomeAssistant,
    mock_api: MagicMock,
    mode: AdditionalWorkMode,
) -> None:
    """Test each writable mode sends its wire value."""
    await setup_integration(hass, mock_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {ATTR_ENTITY_ID: ADDITIONAL_WORK_MODE, ATTR_OPTION: mode.option},
        blocking=True,
    )

    mock_api.async_set_param.assert_awaited_once_with("20", mode.value)


async def test_additional_work_mode_write_failure_surfaces(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test newParam failures raise HomeAssistantError and keep state."""
    mock_api.async_set_param = AsyncMock(
        side_effect=PlumEconetConnectionError("newParam write failed")
    )
    await setup_integration(hass, mock_api)

    with pytest.raises(HomeAssistantError, match="Failed to set additional work mode"):
        await hass.services.async_call(
            "select",
            "select_option",
            {
                ATTR_ENTITY_ID: ADDITIONAL_WORK_MODE,
                ATTR_OPTION: AdditionalWorkMode.OUTSIDE.option,
            },
            blocking=True,
        )

    assert hass.states.get(ADDITIONAL_WORK_MODE).state == AdditionalWorkMode.OFF.option


async def test_additional_work_mode_rejects_selecting_unknown(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test Unsupported is display-only and cannot be written."""
    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKWS4": 3},
    }
    await setup_integration(hass, mock_api)

    assert hass.states.get(ADDITIONAL_WORK_MODE).state == OPTION_UNSUPPORTED

    with pytest.raises(HomeAssistantError, match="read-only"):
        await hass.services.async_call(
            "select",
            "select_option",
            {ATTR_ENTITY_ID: ADDITIONAL_WORK_MODE, ATTR_OPTION: OPTION_UNSUPPORTED},
            blocking=True,
        )
    mock_api.async_set_param.assert_not_awaited()
