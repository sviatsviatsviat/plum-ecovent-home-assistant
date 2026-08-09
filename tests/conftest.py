"""Shared fixtures for Plum ecoVENT tests."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plum_ecovent.api import PlumEconetApi
from custom_components.plum_ecovent.const import CONF_ALLOW_INSECURE_HTTP, DOMAIN

TEST_HOST = "192.0.2.10"
TEST_USERNAME = "admin"
TEST_PASSWORD = "secret"
TEST_UID = "TESTUID1234567890ABC"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in all tests."""


def mock_config_entry() -> MockConfigEntry:
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


async def setup_integration(
    hass: HomeAssistant, mock_api: MagicMock
) -> MockConfigEntry:
    """Set up the integration with the mocked API."""
    entry = mock_config_entry()
    entry.add_to_hass(hass)
    with patch(
        "custom_components.plum_ecovent.PlumEconetApi",
        return_value=mock_api,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


@pytest.fixture
def sys_params() -> dict[str, Any]:
    """Minimal sysParams payload."""
    return {
        "uid": TEST_UID,
        "controllerID": "ecoVENT",
        "softVer": "3.2.3881",
        "moduleASoftVer": "S003.80",
        "regRefresh": 5,
        "settingsVer": 100,
        "password": "device-password",
        "login": "device-login",
        "key": "wifi-key",
        "ssid": "wifi-ssid",
        "servicePassword": "service-secret",
        "wifi": True,
        "wlan0": "192.0.2.20",
        "signal": "-60",
        "quality": 72,
    }


@pytest.fixture
def reg_params() -> dict[str, Any]:
    """Minimal regParams payload."""
    return {
        "settingsVer": 100,
        "editableParamsVer": 50,
        "curr": {
            "REKcurSupTemp": 21.5,
            "REKcurIntTemp": 5.0,
            "REKcurExtTemp": 22.0,
            "REKcuExhTemp": 18.5,
            "REKcurSupFanSpeed": 0,
            "REKcurExhFanSpeed": 0,
            "REKWS1": 6,
            "REKWS4": 0,
            "BYPmodState": 0,
            "BYPcurControl": 0.0,
            "REKUser1SupFanSpeed": 40,
            "REKUser1ExhFanSpeed": 40,
            "REKUser1SetPoint": 20,
            "REKUser2SupFanSpeed": 50,
            "REKUser2ExhFanSpeed": 50,
            "REKUser2SetPoint": 21,
            "REKUser3SupFanSpeed": 60,
            "REKUser3ExhFanSpeed": 60,
            "REKUser3SetPoint": 22,
            "REKPartyExhFanSpeed": 40,
            "REKPartyDur": 3,
            "REKPartySetPoint": 20,
            "REKAiringExhFanSpeed": 50,
            "REKAiringDur": 20,
        },
        "currUnits": {
            "REKcurSupTemp": 1,
            "REKcurIntTemp": 1,
            "REKcurExtTemp": 1,
            "REKcuExhTemp": 1,
            "REKcurSupFanSpeed": 6,
            "REKcurExhFanSpeed": 6,
        },
        "currNumbers": {
            "REKcurSupTemp": 34,
            "REKcurIntTemp": 40,
            "REKcurExtTemp": 36,
            "REKcuExhTemp": 37,
            "REKcurSupFanSpeed": 30,
            "REKcurExhFanSpeed": 31,
            "REKWS1": 17,
            "REKWS4": 20,
            "BYPmodState": 235,
            "BYPcurControl": 343,
            "REKUser1SupFanSpeed": 273,
            "REKUser1ExhFanSpeed": 276,
            "REKUser1SetPoint": 286,
            "REKUser2SupFanSpeed": 274,
            "REKUser2ExhFanSpeed": 277,
            "REKUser2SetPoint": 287,
            "REKUser3SupFanSpeed": 275,
            "REKUser3ExhFanSpeed": 278,
            "REKUser3SetPoint": 288,
            "REKPartyExhFanSpeed": 260,
            "REKPartyDur": 141,
            "REKPartySetPoint": 261,
            "REKAiringExhFanSpeed": 75,
            "REKAiringDur": 143,
        },
    }


def _user_mode_data_entry(
    name: str,
    *,
    value: float,
    unit: int,
    minv: float,
    maxv: float,
) -> dict[str, Any]:
    """Build an editable User Mode data entry."""
    return {
        "name": name,
        "value": value,
        "edit": True,
        "minv": minv,
        "maxv": maxv,
        "mult": 1,
        "unit": unit,
    }


@pytest.fixture
def edit_params() -> dict[str, Any]:
    """Minimal editParams payload."""
    return {
        "editableParamsVer": 50,
        "data": {
            "34": {
                "name": "REKcurSupTemp",
                "value": 21.5,
                "edit": False,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 1,
            },
            "17": {
                "name": "REKWS1",
                "value": 6,
                "edit": True,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 0,
            },
            "20": {
                "name": "REKWS4",
                "value": 0,
                "edit": True,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 0,
            },
            "342": {
                "name": "BYPmodSett",
                "value": 289,
                "edit": True,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 0,
            },
            "235": {
                "name": "BYPmodState",
                "value": 0,
                "edit": True,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 0,
            },
            "343": {
                "name": "BYPcurControl",
                "value": 0.0,
                "edit": True,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 6,
            },
            "18": {
                "name": "REKWS2",
                "value": 5,
                "edit": True,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 0,
            },
            "137": {
                "name": "REKwinterActiveTemp",
                "value": 0,
                "edit": True,
                "minv": -20,
                "maxv": 20,
                "mult": 1,
                "unit": 0,
            },
            "138": {
                "name": "REKsummerHyst",
                "value": 2,
                "edit": True,
                "minv": 0,
                "maxv": 20,
                "mult": 1,
                "unit": 0,
            },
            "273": _user_mode_data_entry(
                "REKUser1SupFanSpeed", value=40, unit=6, minv=20, maxv=100
            ),
            "276": _user_mode_data_entry(
                "REKUser1ExhFanSpeed", value=40, unit=6, minv=20, maxv=100
            ),
            "286": _user_mode_data_entry(
                "REKUser1SetPoint", value=20, unit=1, minv=8, maxv=30
            ),
            "274": _user_mode_data_entry(
                "REKUser2SupFanSpeed", value=50, unit=6, minv=20, maxv=100
            ),
            "277": _user_mode_data_entry(
                "REKUser2ExhFanSpeed", value=50, unit=6, minv=20, maxv=100
            ),
            "287": _user_mode_data_entry(
                "REKUser2SetPoint", value=21, unit=1, minv=8, maxv=30
            ),
            "275": _user_mode_data_entry(
                "REKUser3SupFanSpeed", value=60, unit=6, minv=20, maxv=100
            ),
            "278": _user_mode_data_entry(
                "REKUser3ExhFanSpeed", value=60, unit=6, minv=20, maxv=100
            ),
            # Modes 3–4 may advertise unit 0 while still being °C in the UI.
            "288": _user_mode_data_entry(
                "REKUser3SetPoint", value=22, unit=0, minv=8, maxv=30
            ),
            "469": _user_mode_data_entry(
                "REKUser4SupFanSpeed", value=70, unit=6, minv=20, maxv=100
            ),
            "470": _user_mode_data_entry(
                "REKUser4ExhFanSpeed", value=70, unit=6, minv=20, maxv=100
            ),
            "468": _user_mode_data_entry(
                "REKUser4SetPoint", value=23, unit=0, minv=8, maxv=30
            ),
            "74": {
                "name": "REKPartySupFanSpeed",
                "value": 40,
                "edit": True,
                "minv": 20,
                "maxv": 100,
                "mult": 1,
                "unit": 6,
            },
            "260": {
                "name": "REKPartyExhFanSpeed",
                "value": 40,
                "edit": True,
                "minv": 20,
                "maxv": 100,
                "mult": 1,
                "unit": 6,
            },
            "141": {
                "name": "REKPartyDur",
                "value": 3,
                "edit": True,
                "minv": 0,
                "maxv": 10,
                "mult": 1,
                "unit": 4,
            },
            "261": {
                "name": "REKPartySetPoint",
                "value": 20,
                "edit": True,
                "minv": 8,
                "maxv": 30,
                "mult": 1,
                "unit": 1,
            },
            "142": {
                "name": "REKOutDur",
                "value": 2,
                "edit": True,
                "minv": 0,
                "maxv": 10,
                "mult": 1,
                "unit": 4,
            },
            "75": {
                "name": "REKAiringExhFanSpeed",
                "value": 50,
                "edit": True,
                "minv": 20,
                "maxv": 100,
                "mult": 1,
                "unit": 6,
            },
            "143": {
                "name": "REKAiringDur",
                "value": 20,
                "edit": True,
                "minv": 0,
                "maxv": 20,
                "mult": 1,
                "unit": 3,
            },
            "444": {
                "name": "REKtimeToEndParty",
                "value": -1,
                "edit": False,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 4,
            },
            "445": {
                "name": "REKtimeToEndOut",
                "value": -1,
                "edit": False,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 4,
            },
            "446": {
                "name": "REKtimeToEndAiring",
                "value": -1,
                "edit": False,
                "minv": 0,
                "maxv": 0,
                "mult": 1,
                "unit": 3,
            },
        },
    }


@pytest.fixture
def mock_api(
    sys_params: dict[str, Any],
    reg_params: dict[str, Any],
    edit_params: dict[str, Any],
) -> MagicMock:
    """Mock PlumEconetApi with successful responses."""
    api = MagicMock(spec=PlumEconetApi)
    api.async_get_sys_params = AsyncMock(return_value=sys_params)
    api.async_get_reg_params = AsyncMock(return_value=dict(reg_params))
    api.async_get_edit_params = AsyncMock(return_value=edit_params)
    api.async_set_param = AsyncMock(
        return_value={"paramName": "17", "paramValue": 3, "result": "OK"}
    )
    api.__repr__ = MagicMock(
        return_value=f"PlumEconetApi(host='http://{TEST_HOST}', username='{TEST_USERNAME}')"
    )
    return api
