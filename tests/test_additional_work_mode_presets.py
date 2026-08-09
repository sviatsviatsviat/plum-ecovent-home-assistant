"""Tests for additional / timed work mode number and countdown entities."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.number import ATTR_MODE, NumberMode
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_UNAVAILABLE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.plum_ecovent.exceptions import PlumEconetConnectionError
from custom_components.plum_ecovent.models.additional_work_presets import (
    ADDITIONAL_WORK_MODE_COUNTDOWNS,
    ADDITIONAL_WORK_MODE_NUMBERS,
    resolve_additional_work_mode_countdown,
    resolve_additional_work_mode_number,
)
from custom_components.plum_ecovent.parameters import (
    resolve_readonly_number_param,
    resolve_writable_number_param,
)
from tests.conftest import TEST_UID, setup_integration

PARTY_SUPPLY = "number.plum_ecovent_party_supply_fan_speed"
PARTY_EXHAUST = "number.plum_ecovent_party_exhaust_fan_speed"
PARTY_DURATION = "number.plum_ecovent_party_duration"
PARTY_SETPOINT = "number.plum_ecovent_party_target_temperature"
OUTSIDE_DURATION = "number.plum_ecovent_outside_duration"
AIRING_EXHAUST = "number.plum_ecovent_airing_exhaust_fan_speed"
AIRING_DURATION = "number.plum_ecovent_airing_duration"

PARTY_REMAINING = "sensor.plum_ecovent_party_remaining_time"
OUTSIDE_REMAINING = "sensor.plum_ecovent_outside_remaining_time"
AIRING_REMAINING = "sensor.plum_ecovent_airing_remaining_time"

NUMBER_ENTITY_IDS = (
    PARTY_SUPPLY,
    PARTY_EXHAUST,
    PARTY_DURATION,
    PARTY_SETPOINT,
    OUTSIDE_DURATION,
    AIRING_EXHAUST,
    AIRING_DURATION,
)


def _number_spec(key: str):
    """Return the preset number spec for ``key``."""
    return next(spec for spec in ADDITIONAL_WORK_MODE_NUMBERS if spec.key == key)


def _countdown_spec(key: str):
    """Return the countdown spec for ``key``."""
    return next(spec for spec in ADDITIONAL_WORK_MODE_COUNTDOWNS if spec.key == key)


def test_resolve_writable_number_prefers_curr(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test curr value wins over editParams.data when both are present."""
    status = resolve_writable_number_param(
        reg_params,
        edit_params,
        name="REKPartyExhFanSpeed",
        expected_id=260,
        fallback_min=20,
        fallback_max=100,
    )
    assert status.valid is True
    assert status.value == 40.0
    assert status.min_value == 20.0
    assert status.max_value == 100.0
    assert status.param_id == 260


def test_resolve_writable_number_falls_back_to_edit_params(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test Party supply and Outside duration read from editParams only."""
    party_sup = resolve_additional_work_mode_number(
        reg_params, edit_params, _number_spec("party_supply_fan_speed")
    )
    assert party_sup.valid is True
    assert party_sup.value == 40.0
    assert party_sup.param_id == 74

    outside = resolve_additional_work_mode_number(
        reg_params, edit_params, _number_spec("outside_duration")
    )
    assert outside.valid is True
    assert outside.value == 2.0
    assert outside.param_id == 142


def test_resolve_writable_number_rejects_id_mismatch(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test a wrong data key makes the number unavailable."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("74")
    edit_params["data"]["99"] = entry

    status = resolve_additional_work_mode_number(
        reg_params, edit_params, _number_spec("party_supply_fan_speed")
    )
    assert status.valid is False


def test_resolve_writable_number_rejects_non_editable(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test edit:false makes a writable preset unavailable."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["143"]["edit"] = False

    status = resolve_additional_work_mode_number(
        reg_params, edit_params, _number_spec("airing_duration")
    )
    assert status.valid is False


def test_resolve_writable_number_uses_fallback_for_degenerate_bounds(
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test minv/maxv of 0/0 falls back to the documented range."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["141"]["minv"] = 0
    edit_params["data"]["141"]["maxv"] = 0

    status = resolve_additional_work_mode_number(
        reg_params, edit_params, _number_spec("party_duration")
    )
    assert status.valid is True
    assert status.min_value == 0.0
    assert status.max_value == 10.0


def test_resolve_readonly_countdown_idle_maps_to_zero(
    edit_params: dict[str, Any],
) -> None:
    """Test remaining-time -1 (idle) maps to 0 minutes."""
    status = resolve_additional_work_mode_countdown(
        edit_params, _countdown_spec("party_remaining_time")
    )
    assert status.valid is True
    assert status.value == 0.0


def test_resolve_readonly_countdown_positive_minutes(
    edit_params: dict[str, Any],
) -> None:
    """Test a positive countdown reports remaining minutes."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["444"]["value"] = 178
    edit_params["data"]["445"]["value"] = 55
    edit_params["data"]["446"]["value"] = 19

    party = resolve_readonly_number_param(
        edit_params, name="REKtimeToEndParty", expected_id=444
    )
    assert party.valid is True
    assert party.value == 178.0

    outside = resolve_additional_work_mode_countdown(
        edit_params, _countdown_spec("outside_remaining_time")
    )
    assert outside.valid is True
    assert outside.value == 55.0

    airing = resolve_additional_work_mode_countdown(
        edit_params, _countdown_spec("airing_remaining_time")
    )
    assert airing.valid is True
    assert airing.value == 19.0


async def test_additional_work_mode_numbers_setup_states(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test preset numbers expose live values, units, and unique ids."""
    await setup_integration(hass, mock_api)

    assert hass.states.get(PARTY_SUPPLY).state == "40.0"
    assert hass.states.get(PARTY_EXHAUST).state == "40.0"
    assert hass.states.get(PARTY_DURATION).state == "3.0"
    assert hass.states.get(PARTY_SETPOINT).state == "20.0"
    assert hass.states.get(OUTSIDE_DURATION).state == "2.0"
    assert hass.states.get(AIRING_EXHAUST).state == "50.0"
    assert hass.states.get(AIRING_DURATION).state == "20.0"

    assert (
        hass.states.get(PARTY_DURATION).attributes["unit_of_measurement"]
        == UnitOfTime.HOURS
    )
    assert (
        hass.states.get(AIRING_DURATION).attributes["unit_of_measurement"]
        == UnitOfTime.MINUTES
    )
    assert (
        hass.states.get(PARTY_SETPOINT).attributes["unit_of_measurement"]
        == UnitOfTemperature.CELSIUS
    )
    assert hass.states.get(PARTY_SUPPLY).attributes[ATTR_MODE] == NumberMode.SLIDER
    assert hass.states.get(PARTY_DURATION).attributes[ATTR_MODE] == NumberMode.SLIDER

    registry = er.async_get(hass)
    for entity_id, key in (
        (PARTY_SUPPLY, "party_supply_fan_speed"),
        (OUTSIDE_DURATION, "outside_duration"),
        (AIRING_DURATION, "airing_duration"),
    ):
        entry = registry.async_get(entity_id)
        assert entry is not None
        assert entry.unique_id == f"{TEST_UID}_{key}"


async def test_additional_work_mode_numbers_unavailable_on_id_mismatch(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test id mismatch marks Outside duration unavailable and skips writes."""
    edit_params = deepcopy(edit_params)
    entry = edit_params["data"].pop("142")
    edit_params["data"]["999"] = entry
    mock_api.async_get_edit_params.return_value = edit_params

    await setup_integration(hass, mock_api)

    state = hass.states.get(OUTSIDE_DURATION)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: OUTSIDE_DURATION, "value": 4},
        blocking=True,
    )
    mock_api.async_set_param.assert_not_awaited()


async def test_additional_work_mode_number_write_uses_numeric_id(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test writing Party duration uses newParamName=141 and refreshes."""
    await setup_integration(hass, mock_api)

    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKPartyDur": 4},
    }
    mock_api.async_get_edit_params.return_value = {
        **edit_params,
        "data": {
            **edit_params["data"],
            "141": {**edit_params["data"]["141"], "value": 4},
        },
    }

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: PARTY_DURATION, "value": 4},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with("141", 4)
    assert hass.states.get(PARTY_DURATION).state == "4.0"


async def test_additional_work_mode_number_write_edit_params_only(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test Outside duration write uses id 142 (editParams-only param)."""
    await setup_integration(hass, mock_api)

    mock_api.async_get_edit_params.return_value = {
        **edit_params,
        "data": {
            **edit_params["data"],
            "142": {**edit_params["data"]["142"], "value": 5},
        },
    }

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: OUTSIDE_DURATION, "value": 5},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_api.async_set_param.assert_awaited_once_with("142", 5)
    assert hass.states.get(OUTSIDE_DURATION).state == "5.0"


async def test_additional_work_mode_number_write_failure_surfaces(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test newParam failures raise HomeAssistantError and keep state."""
    mock_api.async_set_param = AsyncMock(
        side_effect=PlumEconetConnectionError("newParam write failed")
    )
    await setup_integration(hass, mock_api)

    with pytest.raises(HomeAssistantError, match="Failed to set REKAiringDur"):
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: AIRING_DURATION, "value": 10},
            blocking=True,
        )

    assert hass.states.get(AIRING_DURATION).state == "20.0"


async def test_additional_work_mode_number_rejects_out_of_range(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test values outside minv/maxv are rejected before writing."""
    from homeassistant.exceptions import ServiceValidationError

    await setup_integration(hass, mock_api)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: PARTY_SUPPLY, "value": 10},
            blocking=True,
        )
    mock_api.async_set_param.assert_not_awaited()


async def test_countdown_sensors_idle_zero(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test idle countdowns (-1) report 0 with the off icon."""
    await setup_integration(hass, mock_api)

    for entity_id in (PARTY_REMAINING, OUTSIDE_REMAINING, AIRING_REMAINING):
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == "0.0"
        assert state.attributes["icon"] == "mdi:timer-sand-complete"
        assert state.attributes["unit_of_measurement"] == UnitOfTime.MINUTES


async def test_countdown_sensors_active_minutes(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test active countdowns expose remaining minutes and unique ids."""
    edit_params = deepcopy(edit_params)
    edit_params["data"]["444"]["value"] = 178
    edit_params["data"]["445"]["value"] = 90
    edit_params["data"]["446"]["value"] = 19
    mock_api.async_get_edit_params.return_value = edit_params

    await setup_integration(hass, mock_api)

    assert hass.states.get(PARTY_REMAINING).state == "178.0"
    assert hass.states.get(OUTSIDE_REMAINING).state == "90.0"
    assert hass.states.get(AIRING_REMAINING).state == "19.0"
    assert hass.states.get(PARTY_REMAINING).attributes["icon"] == "mdi:timer-sand"
    assert (
        hass.states.get(PARTY_REMAINING).attributes["unit_of_measurement"]
        == UnitOfTime.MINUTES
    )

    registry = er.async_get(hass)
    entry = registry.async_get(PARTY_REMAINING)
    assert entry is not None
    assert entry.unique_id == f"{TEST_UID}_party_remaining_time"


async def test_all_preset_numbers_present(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test every documented additional-mode number entity is created."""
    await setup_integration(hass, mock_api)

    for entity_id in NUMBER_ENTITY_IDS:
        assert hass.states.get(entity_id) is not None
