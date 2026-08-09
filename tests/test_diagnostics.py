"""Tests for Plum ecoVENT diagnostics."""

from unittest.mock import MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plum_ecovent.const import CONF_ALLOW_INSECURE_HTTP, DOMAIN
from custom_components.plum_ecovent.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.conftest import TEST_HOST, TEST_PASSWORD, TEST_UID, TEST_USERNAME


async def test_diagnostics_redact_secrets(hass, mock_api: MagicMock) -> None:
    """Test that diagnostics redact host, credentials, and sensitive fields."""
    assert await async_setup_component(hass, "diagnostics", {})
    mock_api.async_get_sys_params.return_value = {
        **mock_api.async_get_sys_params.return_value,
        "wlan0": TEST_HOST,
    }

    entry = MockConfigEntry(
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
    entry.add_to_hass(hass)

    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, entry)

    serialized = str(result)
    assert TEST_HOST not in serialized
    assert TEST_USERNAME not in serialized
    assert TEST_PASSWORD not in serialized
    assert "device-password" not in serialized
    assert "service-secret" not in serialized
    assert "wifi-key" not in serialized
    assert "wifi-ssid" not in serialized
    assert result["entry"]["unique_id"] == TEST_UID
    assert "REKcurSupTemp" in result["reg_params"]["curr_keys"]
    assert result["wifi"] == {
        "wifi": True,
        "signal": -60.0,
        "quality": 72.0,
    }
    assert "wlan0" not in result["wifi"]
    assert "ssid" not in result["wifi"]
    assert result["sys_params"]["ssid"] != "wifi-ssid"
