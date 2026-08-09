"""Tests for Plum ecoVENT Wi-Fi diagnostic sensors."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    STATE_UNAVAILABLE,
    EntityCategory,
)
from homeassistant.helpers import entity_registry as er

from custom_components.plum_ecovent.const import DOMAIN
from tests.conftest import TEST_UID, setup_integration


def _wifi_entity_ids(hass) -> tuple[str, str]:
    """Resolve Wi-Fi sensor entity IDs by unique_id."""
    registry = er.async_get(hass)
    signal_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{TEST_UID}_wifi_signal"
    )
    quality_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{TEST_UID}_wifi_quality"
    )
    assert signal_id is not None
    assert quality_id is not None
    return signal_id, quality_id


async def _enable_wifi_sensors(hass, mock_api: MagicMock) -> tuple[str, str]:
    """Enable disabled-by-default diagnostic Wi-Fi sensors."""
    registry = er.async_get(hass)
    signal_id, quality_id = _wifi_entity_ids(hass)
    for entity_id in (signal_id, quality_id):
        entry = registry.async_get(entity_id)
        assert entry is not None
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        registry.async_update_entity(entity_id, disabled_by=None)
    config_entry = next(iter(hass.config_entries.async_entries(DOMAIN)))
    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()
    return signal_id, quality_id


async def test_wifi_sensors_are_diagnostic_and_disabled_by_default(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test Wi-Fi sensors use EntityCategory.DIAGNOSTIC and start disabled."""
    await setup_integration(hass, mock_api)

    registry = er.async_get(hass)
    signal_id, quality_id = _wifi_entity_ids(hass)
    for entity_id, unique_suffix in (
        (signal_id, "wifi_signal"),
        (quality_id, "wifi_quality"),
    ):
        entry = registry.async_get(entity_id)
        assert entry is not None
        assert entry.unique_id == f"{TEST_UID}_{unique_suffix}"
        assert entry.entity_category is EntityCategory.DIAGNOSTIC
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        assert hass.states.get(entity_id) is None


async def test_wifi_sensors_report_signal_and_quality(
    hass,
    mock_api: MagicMock,
) -> None:
    """Test enabled Wi-Fi sensors report sysParams signal dBm and quality %."""
    await setup_integration(hass, mock_api)
    signal_id, quality_id = await _enable_wifi_sensors(hass, mock_api)

    signal = hass.states.get(signal_id)
    quality = hass.states.get(quality_id)
    assert signal is not None
    assert quality is not None
    assert signal.state == "-60.0"
    assert quality.state == "72.0"
    assert (
        signal.attributes[ATTR_UNIT_OF_MEASUREMENT]
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )
    assert quality.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE


async def test_wifi_sensors_track_sys_params_refresh(
    hass,
    mock_api: MagicMock,
    sys_params: dict[str, Any],
) -> None:
    """Test Wi-Fi sensors follow coordinator sysParams refresh."""
    entry = await setup_integration(hass, mock_api)
    signal_id, quality_id = await _enable_wifi_sensors(hass, mock_api)

    mock_api.async_get_sys_params.return_value = {
        **sys_params,
        "signal": "-48",
        "quality": 88,
    }
    await entry.runtime_data.async_request_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(signal_id).state == "-48.0"
    assert hass.states.get(quality_id).state == "88.0"


async def test_wifi_sensors_unavailable_when_fields_missing(
    hass,
    mock_api: MagicMock,
    sys_params: dict[str, Any],
) -> None:
    """Test missing Wi-Fi fields mark the diagnostic sensors unavailable."""
    params = {**sys_params}
    params.pop("signal")
    params.pop("quality")
    mock_api.async_get_sys_params.return_value = params
    await setup_integration(hass, mock_api)
    signal_id, quality_id = await _enable_wifi_sensors(hass, mock_api)

    assert hass.states.get(signal_id).state == STATE_UNAVAILABLE
    assert hass.states.get(quality_id).state == STATE_UNAVAILABLE
