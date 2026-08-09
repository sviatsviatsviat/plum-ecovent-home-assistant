"""Tests for Plum ecoVENT summer / winter mode select and setpoints."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_OPTION,
    STATE_UNAVAILABLE,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.plum_ecovent.exceptions import PlumEconetConnectionError
from custom_components.plum_ecovent.models.summer_winter import (
    OPTION_UNSUPPORTED,
    SUMMER_WINTER_MODES,
    SummerWinterMode,
    resolve_summer_hysteresis,
    resolve_summer_winter_mode,
    resolve_winter_active_temp,
)
from tests.conftest import TEST_UID, setup_integration

SUMMER_WINTER_MODE = "select.plum_ecovent_summer_winter_mode"
WINTER_ACTIVE_TEMP = "number.plum_ecovent_winter_mode_turn_on_temperature"
SUMMER_HYSTERESIS = "number.plum_ecovent_summer_mode_hysteresis"

WIRE_CASES = (
    *((mode.value, mode.option) for mode in SUMMER_WINTER_MODES),
    (0, OPTION_UNSUPPORTED),
    (3, OPTION_UNSUPPORTED),
    (4, OPTION_UNSUPPORTED),
    (6, OPTION_UNSUPPORTED),
)


def test_summer_winter_mode_enum_wires() -> None:
    """Test SummerWinterMode encapsulates wire values and option keys."""
    assert SummerWinterMode.SUMMER == 1
    assert SummerWinterMode.WINTER == 2
    assert SummerWinterMode.AUTO == 5
    assert SummerWinterMode.VENTILATION == 8
    assert SummerWinterMode.AUTO.option == "auto"
    assert SummerWinterMode.from_wire(2) is SummerWinterMode.WINTER
    assert SummerWinterMode.from_wire(0) is None
    assert SummerWinterMode.from_option("ventilation") is SummerWinterMode.VENTILATION
    assert [mode.option for mode in SUMMER_WINTER_MODES] == [
        "summer",
        "winter",
        "auto",
        "ventilation",
    ]


def test_resolve_summer_winter_mode_accepts_expected_id(
    edit_params: dict[str, Any],
) -> None:
    """Test REKWS2 resolves when name maps to id 18 and is editable."""
    status = resolve_summer_winter_mode(edit_params)
    assert status.valid is True
    assert status.wire == SummerWinterMode.AUTO
    assert status.mode is SummerWinterMode.AUTO
    assert status.option == SummerWinterMode.AUTO.option


def test_resolve_summer_winter_mode_rejects_id_mismatch(
    edit_params: dict[str, Any],
) -> None:
    """Test a wrong data key for REKWS2 makes the entity unavailable."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("18")
    edit_params["data"]["99"] = entry

    status = resolve_summer_winter_mode(edit_params)
    assert status.valid is False
    assert status.option is None


def test_resolve_summer_winter_mode_rejects_missing_name(
    edit_params: dict[str, Any],
) -> None:
    """Test missing REKWS2 in editParams.data is unavailable."""
    edit_params = deepcopy(edit_params)
    del edit_params["data"]["18"]

    assert resolve_summer_winter_mode(edit_params).valid is False


def test_resolve_summer_winter_mode_rejects_non_editable(
    edit_params: dict[str, Any],
) -> None:
    """Test edit:false REKWS2 is unavailable."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["18"]["edit"] = False

    assert resolve_summer_winter_mode(edit_params).valid is False


def test_resolve_summer_winter_mode_rejects_curr_numbers_mismatch(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test currNumbers disagreeing with id 18 is unavailable."""
    reg_params = deepcopy(reg_params)
    reg_params["currNumbers"]["REKWS2"] = 99

    assert resolve_summer_winter_mode(edit_params, reg_params).valid is False


def test_resolve_setpoints_accept_expected_ranges(
    edit_params: dict[str, Any],
) -> None:
    """Test winter temp and summer hysteresis resolve with module bounds."""
    winter = resolve_winter_active_temp(edit_params)
    assert winter.valid is True
    assert winter.value == 0.0
    assert winter.min_value == -20.0
    assert winter.max_value == 20.0

    summer = resolve_summer_hysteresis(edit_params)
    assert summer.valid is True
    assert summer.value == 2.0
    assert summer.min_value == 0.0
    assert summer.max_value == 20.0


def test_resolve_setpoints_use_fallbacks_for_inverted_bounds(
    edit_params: dict[str, Any],
) -> None:
    """Test inverted minv/maxv falls back to the documented range."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["137"]["minv"] = 10
    edit_params["data"]["137"]["maxv"] = -5

    winter = resolve_winter_active_temp(edit_params)
    assert winter.valid is True
    assert winter.value == 0.0
    assert winter.min_value == -20.0
    assert winter.max_value == 20.0


def test_resolve_setpoints_use_fallbacks_for_degenerate_zero_bounds(
    edit_params: dict[str, Any],
) -> None:
    """Test minv/maxv of 0/0 falls back to the documented ranges."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["137"]["minv"] = 0
    edit_params["data"]["137"]["maxv"] = 0
    edit_params["data"]["138"]["minv"] = 0
    edit_params["data"]["138"]["maxv"] = 0

    winter = resolve_winter_active_temp(edit_params)
    assert winter.valid is True
    assert winter.min_value == -20.0
    assert winter.max_value == 20.0

    summer = resolve_summer_hysteresis(edit_params)
    assert summer.valid is True
    assert summer.min_value == 0.0
    assert summer.max_value == 20.0


@pytest.mark.parametrize(("wire", "option"), WIRE_CASES)
async def test_summer_winter_mode_maps_wire_values(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
    wire: int,
    option: str,
) -> None:
    """Test Summer/Winter/Auto/Ventilation wires and Unsupported otherwise."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["18"]["value"] = wire
    mock_api.async_get_edit_params.return_value = edit_params
    await setup_integration(hass, mock_api)

    state = hass.states.get(SUMMER_WINTER_MODE)
    assert state is not None
    assert state.state == option
    assert SummerWinterMode.SUMMER.option in state.attributes["options"]
    if option == OPTION_UNSUPPORTED:
        assert OPTION_UNSUPPORTED in state.attributes["options"]
    else:
        assert OPTION_UNSUPPORTED not in state.attributes["options"]


async def test_summer_winter_mode_unique_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test the select unique id is keyed by module uid."""
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    entry = registry.async_get(SUMMER_WINTER_MODE)
    assert entry is not None
    assert entry.unique_id == f"{TEST_UID}_summer_winter_mode"
    assert entry.entity_category is EntityCategory.CONFIG


async def test_summer_winter_mode_unavailable_on_id_mismatch(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test id mismatch marks the select unavailable and skips writes."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("18")
    edit_params["data"]["99"] = entry
    mock_api.async_get_edit_params.return_value = edit_params

    await setup_integration(hass, mock_api)

    state = hass.states.get(SUMMER_WINTER_MODE)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: SUMMER_WINTER_MODE,
            ATTR_OPTION: SummerWinterMode.SUMMER.option,
        },
        blocking=True,
    )
    mock_api.async_set_param.assert_not_awaited()


async def test_summer_winter_mode_write_uses_numeric_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test selecting Winter writes newParamName=18 and refreshes editParams."""
    await setup_integration(hass, mock_api)

    refreshed = deepcopy(edit_params)
    refreshed["data"]["18"]["value"] = SummerWinterMode.WINTER
    mock_api.async_get_edit_params.return_value = refreshed

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: SUMMER_WINTER_MODE,
            ATTR_OPTION: SummerWinterMode.WINTER.option,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with(
        "18", SummerWinterMode.WINTER.value
    )
    assert hass.states.get(SUMMER_WINTER_MODE).state == SummerWinterMode.WINTER.option


@pytest.mark.parametrize("mode", list(SUMMER_WINTER_MODES))
async def test_summer_winter_mode_write_all_writable_options(
    hass: HomeAssistant,
    mock_api: MagicMock,
    mode: SummerWinterMode,
) -> None:
    """Test each writable mode sends its wire value."""
    await setup_integration(hass, mock_api)

    await hass.services.async_call(
        "select",
        "select_option",
        {ATTR_ENTITY_ID: SUMMER_WINTER_MODE, ATTR_OPTION: mode.option},
        blocking=True,
    )

    mock_api.async_set_param.assert_awaited_once_with("18", mode.value)


async def test_summer_winter_mode_write_failure_surfaces(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test newParam failures raise HomeAssistantError and keep state."""
    mock_api.async_set_param = AsyncMock(
        side_effect=PlumEconetConnectionError("Got 500")
    )
    await setup_integration(hass, mock_api)

    with pytest.raises(HomeAssistantError, match="Failed to set summer / winter mode"):
        await hass.services.async_call(
            "select",
            "select_option",
            {
                ATTR_ENTITY_ID: SUMMER_WINTER_MODE,
                ATTR_OPTION: SummerWinterMode.SUMMER.option,
            },
            blocking=True,
        )

    assert hass.states.get(SUMMER_WINTER_MODE).state == SummerWinterMode.AUTO.option


async def test_summer_winter_mode_rejects_selecting_unknown(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test Unsupported is display-only and cannot be written."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["18"]["value"] = 0
    mock_api.async_get_edit_params.return_value = edit_params
    await setup_integration(hass, mock_api)

    assert hass.states.get(SUMMER_WINTER_MODE).state == OPTION_UNSUPPORTED

    with pytest.raises(HomeAssistantError, match="read-only"):
        await hass.services.async_call(
            "select",
            "select_option",
            {ATTR_ENTITY_ID: SUMMER_WINTER_MODE, ATTR_OPTION: OPTION_UNSUPPORTED},
            blocking=True,
        )
    mock_api.async_set_param.assert_not_awaited()


async def test_setpoint_entities_expose_module_bounds(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test number entities report module min/max and current values."""
    await setup_integration(hass, mock_api)

    winter = hass.states.get(WINTER_ACTIVE_TEMP)
    assert winter is not None
    assert winter.state == "0.0"
    assert winter.attributes["min"] == -20.0
    assert winter.attributes["max"] == 20.0
    assert winter.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS
    assert winter.attributes["mode"] == "slider"

    summer = hass.states.get(SUMMER_HYSTERESIS)
    assert summer is not None
    assert summer.state == "2.0"
    assert summer.attributes["min"] == 0.0
    assert summer.attributes["max"] == 20.0
    assert summer.attributes["mode"] == "slider"


async def test_setpoint_unique_ids(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test number unique ids are keyed by module uid."""
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    winter = registry.async_get(WINTER_ACTIVE_TEMP)
    summer = registry.async_get(SUMMER_HYSTERESIS)
    assert winter is not None
    assert summer is not None
    assert winter.unique_id == f"{TEST_UID}_winter_active_temperature"
    assert summer.unique_id == f"{TEST_UID}_summer_mode_hysteresis"
    assert winter.entity_category is EntityCategory.CONFIG
    assert summer.entity_category is EntityCategory.CONFIG


async def test_winter_active_temp_write_uses_numeric_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test setting winter turn-on temp writes newParamName=137."""
    await setup_integration(hass, mock_api)

    refreshed = deepcopy(edit_params)
    refreshed["data"]["137"]["value"] = -5
    mock_api.async_get_edit_params.return_value = refreshed

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: WINTER_ACTIVE_TEMP, "value": -5},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with("137", -5)
    assert hass.states.get(WINTER_ACTIVE_TEMP).state == "-5.0"


async def test_summer_hysteresis_write_uses_numeric_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test setting summer hysteresis writes newParamName=138."""
    await setup_integration(hass, mock_api)

    refreshed = deepcopy(edit_params)
    refreshed["data"]["138"]["value"] = 4
    mock_api.async_get_edit_params.return_value = refreshed

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: SUMMER_HYSTERESIS, "value": 4},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with("138", 4)
    assert hass.states.get(SUMMER_HYSTERESIS).state == "4.0"


async def test_setpoint_unavailable_on_id_mismatch(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test setpoint id mismatch marks the number unavailable."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("137")
    edit_params["data"]["999"] = entry
    mock_api.async_get_edit_params.return_value = edit_params

    await setup_integration(hass, mock_api)

    assert hass.states.get(WINTER_ACTIVE_TEMP).state == STATE_UNAVAILABLE

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: WINTER_ACTIVE_TEMP, "value": 1},
        blocking=True,
    )
    mock_api.async_set_param.assert_not_awaited()


async def test_setpoint_write_rejects_out_of_range(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test values outside advertised minv/maxv are rejected before writing."""
    from homeassistant.helpers.entity_platform import async_get_platforms

    await setup_integration(hass, mock_api)

    entity = None
    for platform in async_get_platforms(hass, "plum_ecovent"):
        candidate = platform.entities.get(WINTER_ACTIVE_TEMP)
        if candidate is not None:
            entity = candidate
            break
    assert entity is not None

    with pytest.raises(HomeAssistantError, match="outside allowed range"):
        await entity.async_set_native_value(25.0)
    mock_api.async_set_param.assert_not_awaited()

    with pytest.raises(HomeAssistantError, match="outside allowed range"):
        await entity.async_set_native_value(-25.0)
    mock_api.async_set_param.assert_not_awaited()


async def test_setpoint_write_failure_surfaces(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test newParam failures raise HomeAssistantError and keep state."""
    mock_api.async_set_param = AsyncMock(
        side_effect=PlumEconetConnectionError("Got 500")
    )
    await setup_integration(hass, mock_api)

    with pytest.raises(
        HomeAssistantError, match="Failed to set winter mode turn-on temperature"
    ):
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: WINTER_ACTIVE_TEMP, "value": 3},
            blocking=True,
        )

    assert hass.states.get(WINTER_ACTIVE_TEMP).state == "0.0"
