"""Tests for sticky optimistic pending writes on selects and numbers."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from freezegun import freeze_time
from homeassistant.const import ATTR_ASSUMED_STATE, ATTR_ENTITY_ID, ATTR_OPTION
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.plum_ecovent.const import PENDING_WRITE_TIMEOUT
from custom_components.plum_ecovent.exceptions import PlumEconetConnectionError
from custom_components.plum_ecovent.models.operation import OperationMode
from custom_components.plum_ecovent.pending_write import (
    ATTR_PENDING_UNTIL,
    ATTR_PENDING_WRITE,
    PlumEconetPendingWriteMixin,
)
from tests.conftest import setup_integration

OPERATION_MODE = "select.plum_ecovent_recuperation_operation_mode"
WINTER_ACTIVE_TEMP = "number.plum_ecovent_winter_mode_turn_on_temperature"


async def test_select_keeps_pending_while_refresh_is_stale(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test a successful write keeps the new option while curr is still old."""
    entry = await setup_integration(hass, mock_api)

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

    state = hass.states.get(OPERATION_MODE)
    assert state is not None
    assert state.state == OperationMode.MODE_1.option
    assert state.attributes.get(ATTR_ASSUMED_STATE) is True
    assert state.attributes.get(ATTR_PENDING_WRITE) is True
    assert ATTR_PENDING_UNTIL in state.attributes
    mock_api.async_set_param.assert_awaited_once_with(
        "17", OperationMode.MODE_1.value
    )
    # Immediate post-write refresh still ran (stale overlay, not delayed refresh).
    assert mock_api.async_get_reg_params.await_count >= 2

    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(OPERATION_MODE)
    assert state is not None
    assert state.state == OperationMode.MODE_1.option
    assert state.attributes.get(ATTR_PENDING_WRITE) is True


async def test_select_clears_pending_when_device_confirms(
    hass: HomeAssistant,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
) -> None:
    """Test pending clears once regParams returns the written option."""
    entry = await setup_integration(hass, mock_api)

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
    assert hass.states.get(OPERATION_MODE).attributes.get(ATTR_PENDING_WRITE) is True

    mock_api.async_get_reg_params.return_value = {
        **reg_params,
        "curr": {**reg_params["curr"], "REKWS1": OperationMode.MODE_1.value},
    }
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(OPERATION_MODE)
    assert state is not None
    assert state.state == OperationMode.MODE_1.option
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert ATTR_PENDING_WRITE not in state.attributes
    assert ATTR_PENDING_UNTIL not in state.attributes


async def test_select_pending_times_out_to_device_value(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test pending clears after 30s and state falls back to the device."""
    with freeze_time("2026-08-08 12:00:00") as frozen:
        entry = await setup_integration(hass, mock_api)

        await hass.services.async_call(
            "select",
            "select_option",
            {
                ATTR_ENTITY_ID: OPERATION_MODE,
                ATTR_OPTION: OperationMode.MODE_2.option,
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        assert hass.states.get(OPERATION_MODE).state == OperationMode.MODE_2.option
        assert hass.states.get(OPERATION_MODE).attributes.get(ATTR_PENDING_WRITE) is True

        frozen.tick(timedelta(seconds=PENDING_WRITE_TIMEOUT + 1))
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

        state = hass.states.get(OPERATION_MODE)
        assert state is not None
        assert state.state == OperationMode.HALT.option
        assert ATTR_PENDING_WRITE not in state.attributes
        assert ATTR_ASSUMED_STATE not in state.attributes


async def test_select_write_failure_does_not_set_pending(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test a failed newParam leaves state and pending markers unchanged."""
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

    state = hass.states.get(OPERATION_MODE)
    assert state is not None
    assert state.state == OperationMode.HALT.option
    assert ATTR_PENDING_WRITE not in state.attributes
    assert ATTR_ASSUMED_STATE not in state.attributes


async def test_select_second_write_replaces_pending(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test a second write before confirm keeps only the latest pending value."""
    await setup_integration(hass, mock_api)

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
    assert hass.states.get(OPERATION_MODE).state == OperationMode.MODE_1.option

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: OPERATION_MODE,
            ATTR_OPTION: OperationMode.MODE_3.option,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(OPERATION_MODE)
    assert state is not None
    assert state.state == OperationMode.MODE_3.option
    assert state.attributes.get(ATTR_PENDING_WRITE) is True
    assert mock_api.async_set_param.await_count == 2
    mock_api.async_set_param.assert_awaited_with("17", OperationMode.MODE_3.value)


async def test_select_stale_write_does_not_overwrite_newer_pending() -> None:
    """Test an older write sequence cannot replace a newer pending value."""

    class _Probe(PlumEconetPendingWriteMixin):
        def _pending_device_value(self) -> str | None:
            return "halt"

    probe = _Probe()
    older_seq = probe.begin_write()
    newer_seq = probe.begin_write()

    assert probe.set_pending("mode_3", write_seq=newer_seq) is True
    assert probe.pending_active() is True
    assert probe._pending_value == "mode_3"

    assert probe.set_pending("mode_1", write_seq=older_seq) is False
    assert probe._pending_value == "mode_3"
    assert probe.pending_active() is True


async def test_select_pending_expires_without_coordinator_refresh(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test the scheduled expiry clears pending without a coordinator poll."""
    entry = await setup_integration(hass, mock_api)
    coordinator = entry.runtime_data
    coordinator.update_interval = None
    if coordinator._unsub_refresh is not None:
        coordinator._unsub_refresh()
        coordinator._unsub_refresh = None

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: OPERATION_MODE,
            ATTR_OPTION: OperationMode.MODE_2.option,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(OPERATION_MODE).state == OperationMode.MODE_2.option
    assert hass.states.get(OPERATION_MODE).attributes.get(ATTR_PENDING_WRITE) is True

    reg_calls_before = mock_api.async_get_reg_params.await_count
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=PENDING_WRITE_TIMEOUT + 1)
    )
    await hass.async_block_till_done()

    state = hass.states.get(OPERATION_MODE)
    assert state is not None
    assert state.state == OperationMode.HALT.option
    assert ATTR_PENDING_WRITE not in state.attributes
    # Expiry may request a refresh; allow that, but the UI must already fall back.
    assert mock_api.async_get_reg_params.await_count >= reg_calls_before


async def test_number_keeps_pending_while_refresh_is_stale(
    hass: HomeAssistant,
    mock_api: MagicMock,
) -> None:
    """Test a successful number write keeps the setpoint while data is stale."""
    entry = await setup_integration(hass, mock_api)

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: WINTER_ACTIVE_TEMP, "value": -5},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(WINTER_ACTIVE_TEMP)
    assert state is not None
    assert state.state == "-5.0"
    assert state.attributes.get(ATTR_ASSUMED_STATE) is True
    assert state.attributes.get(ATTR_PENDING_WRITE) is True

    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(WINTER_ACTIVE_TEMP)
    assert state is not None
    assert state.state == "-5.0"
    assert state.attributes.get(ATTR_PENDING_WRITE) is True


async def test_number_clears_pending_when_device_confirms(
    hass: HomeAssistant,
    mock_api: MagicMock,
    edit_params: dict[str, Any],
) -> None:
    """Test pending clears once editParams returns the written setpoint."""
    entry = await setup_integration(hass, mock_api)

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: WINTER_ACTIVE_TEMP, "value": -5},
        blocking=True,
    )
    await hass.async_block_till_done()

    refreshed = deepcopy(edit_params)
    refreshed["data"]["137"]["value"] = -5
    mock_api.async_get_edit_params.return_value = refreshed
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(WINTER_ACTIVE_TEMP)
    assert state is not None
    assert state.state == "-5.0"
    assert ATTR_PENDING_WRITE not in state.attributes
    assert ATTR_ASSUMED_STATE not in state.attributes
