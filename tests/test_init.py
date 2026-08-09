"""Tests for Plum ecoVENT config entry setup."""

import logging
from copy import deepcopy
from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.plum_ecovent.api import PlumEconetApi
from custom_components.plum_ecovent.const import CONF_ALLOW_INSECURE_HTTP, DOMAIN
from custom_components.plum_ecovent.coordinator import PlumEconetCoordinator
from custom_components.plum_ecovent.exceptions import (
    PlumEconetAuthError,
    PlumEconetConnectionError,
)
from tests.conftest import (
    TEST_HOST,
    TEST_PASSWORD,
    TEST_UID,
    TEST_USERNAME,
    setup_integration,
)


def _entry() -> MockConfigEntry:
    """Build a config entry with credentials."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="ecoVENT",
        data={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_ALLOW_INSECURE_HTTP: True,
        },
        unique_id=TEST_UID,
    )


async def test_setup_creates_device_and_unloads(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test setup registers the device and unload clears runtime state."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.plum_ecovent_stub_status") is None

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_UID)})
    assert device is not None
    assert device.manufacturer == "Plum"
    assert device.model == "ecoVENT"
    assert device.sw_version == "3.2.3881"
    assert entry.runtime_data is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not hasattr(entry, "runtime_data")


async def test_setup_keeps_polling_without_platforms(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test that the coordinator keeps polling when no platforms listen."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert mock_api.async_get_reg_params.await_count == 1

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()

    assert mock_api.async_get_reg_params.await_count >= 2


async def test_setup_auth_error_does_not_retry_as_not_ready(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test that HTTP 401 during first refresh becomes an auth failure."""
    mock_api.async_get_sys_params = AsyncMock(
        side_effect=PlumEconetAuthError("Invalid credentials")
    )
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_rejects_changed_uid(
    hass,
    mock_api: MagicMock,
    sys_params: dict[str, Any],
) -> None:
    """Test that setup fails when the module uid differs from the entry."""
    sys_params = {**sys_params, "uid": "DIFFERENT-UID"}
    mock_api.async_get_sys_params = AsyncMock(return_value=sys_params)

    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_rejects_missing_uid(
    hass,
    mock_api: MagicMock,
    sys_params: dict[str, Any],
) -> None:
    """Test that setup fails when sysParams omits uid."""
    sys_params = {**sys_params}
    sys_params.pop("uid")
    mock_api.async_get_sys_params = AsyncMock(return_value=sys_params)

    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_defaults_model_to_ecovent(
    hass,
    mock_api: MagicMock,
    sys_params: dict[str, Any],
) -> None:
    """Test that missing controllerID falls back to ecoVENT."""
    sys_params = {**sys_params}
    sys_params.pop("controllerID")
    mock_api.async_get_sys_params = AsyncMock(return_value=sys_params)

    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_UID)})
    assert device is not None
    assert device.model == "ecoVENT"


async def test_setup_rejects_stub_entry_without_host(hass) -> None:
    """Test that a pre-LAN stub entry fails cleanly instead of KeyError."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Plum ecoVENT",
        data={},
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_rejects_cleartext_http_without_opt_in(hass) -> None:
    """Test that host-only entries without insecure HTTP fail cleanly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ecoVENT",
        data={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_ALLOW_INSECURE_HTTP: False,
        },
        unique_id=TEST_UID,
    )
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_passes_insecure_http_opt_in_to_api(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test that setup forwards the insecure-HTTP flag to the API client."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ) as api_cls:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert api_cls.call_args.kwargs["allow_insecure_http"] is True


async def test_coordinator_refetches_edit_params_each_poll(
    hass,
    sys_params: dict[str, Any],
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> None:
    """Test editParams is polled every update for informationParams values."""
    entry = _entry()
    entry.add_to_hass(hass)

    api = MagicMock(spec=PlumEconetApi)
    api.async_get_sys_params = AsyncMock(return_value=sys_params)
    api.async_get_edit_params = AsyncMock(return_value=edit_params)
    api.async_get_reg_params = AsyncMock(
        side_effect=[
            dict(reg_params),
            dict(reg_params),
            {
                **reg_params,
                "editableParamsVer": 51,
                "settingsVer": 101,
            },
        ]
    )

    coordinator = PlumEconetCoordinator(hass, api, entry)
    await coordinator.async_refresh()

    assert api.async_get_edit_params.await_count == 1
    assert coordinator.update_interval == timedelta(seconds=5)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert api.async_get_edit_params.await_count == 2
    assert api.async_get_reg_params.await_count == 2

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert api.async_get_edit_params.await_count == 3
    assert api.async_get_reg_params.await_count == 3


async def test_runtime_uid_change_rejects_entire_snapshot(
    hass,
    mock_api: MagicMock,
    sys_params: dict[str, Any],
) -> None:
    """Test a different device at the host cannot replace the active snapshot."""
    entry = await setup_integration(hass, mock_api)
    coordinator = entry.runtime_data
    accepted = coordinator.data
    reg_calls = mock_api.async_get_reg_params.await_count
    edit_calls = mock_api.async_get_edit_params.await_count

    mock_api.async_get_sys_params.return_value = {
        **sys_params,
        "uid": "DIFFERENT-UID",
        "quality": 1,
    }
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is False
    assert coordinator.data is accepted
    assert coordinator.sys_params["uid"] == TEST_UID
    assert mock_api.async_get_reg_params.await_count == reg_calls
    assert mock_api.async_get_edit_params.await_count == edit_calls


async def test_coordinator_publishes_payloads_atomically(
    hass,
    mock_api: MagicMock,
    sys_params: dict[str, Any],
) -> None:
    """Test a later endpoint failure cannot partially mutate active data."""
    entry = await setup_integration(hass, mock_api)
    coordinator = entry.runtime_data
    accepted = coordinator.data

    mock_api.async_get_sys_params.return_value = {**sys_params, "quality": 1}
    mock_api.async_get_reg_params.side_effect = PlumEconetConnectionError("offline")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.data is accepted
    assert coordinator.sys_params["quality"] == 72


async def test_unexpected_wire_warns_once_per_state_transition(
    hass,
    mock_api: MagicMock,
    reg_params: dict[str, Any],
    caplog,
) -> None:
    """Test a persistent unsupported wire does not warn on every poll."""
    unsupported = deepcopy(reg_params)
    unsupported["curr"]["REKWS1"] = 0
    mock_api.async_get_reg_params.return_value = unsupported

    with caplog.at_level(
        logging.WARNING,
        logger="custom_components.plum_ecovent.coordinator.update",
    ):
        entry = await setup_integration(hass, mock_api)
        await entry.runtime_data.async_refresh()
        await entry.runtime_data.async_refresh()

        mock_api.async_get_reg_params.return_value = reg_params
        await entry.runtime_data.async_refresh()
        mock_api.async_get_reg_params.return_value = unsupported
        await entry.runtime_data.async_refresh()

    messages = [
        record.getMessage()
        for record in caplog.records
        if "Unexpected REKWS1 wire value 0" in record.getMessage()
    ]
    assert len(messages) == 2
