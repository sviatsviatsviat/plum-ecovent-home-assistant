"""Tests for the Plum ecoVENT config flow."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.plum_ecovent.const import CONF_ALLOW_INSECURE_HTTP, DOMAIN
from custom_components.plum_ecovent.exceptions import (
    PlumEconetAuthError,
    PlumEconetConnectionError,
    PlumEconetInsecureHttpError,
)
from tests.conftest import TEST_HOST, TEST_PASSWORD, TEST_UID, TEST_USERNAME


def _user_input(*, allow_insecure_http: bool = False) -> dict:
    """Build typical user-step input."""
    return {
        CONF_HOST: TEST_HOST,
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_ALLOW_INSECURE_HTTP: allow_insecure_http,
    }


async def test_user_flow_creates_entry(hass, sys_params) -> None:
    """Test that a successful probe creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    schema_keys = {key.schema for key in result["data_schema"].schema}
    assert CONF_ALLOW_INSECURE_HTTP in schema_keys

    with (
        patch(
            "custom_components.plum_ecovent.config_flow.PlumEconetApi.async_get_sys_params",
            new=AsyncMock(return_value=sys_params),
        ),
        patch(
            "custom_components.plum_ecovent.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=_user_input(allow_insecure_http=True),
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ecoVENT"
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_ALLOW_INSECURE_HTTP: True,
    }
    assert result["result"].unique_id == TEST_UID


async def test_user_flow_insecure_http_required(hass) -> None:
    """Test that missing insecure-HTTP opt-in surfaces a clear form error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    with patch(
        "custom_components.plum_ecovent.config_flow.PlumEconetApi",
        side_effect=PlumEconetInsecureHttpError("needs opt-in"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=_user_input(allow_insecure_http=False),
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "insecure_http_required"}


def test_user_flow_warns_about_insecure_http() -> None:
    """Test that translations warn when Allow insecure HTTP is offered."""
    strings = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "custom_components"
            / "plum_ecovent"
            / "translations"
            / "en.json"
        ).read_text(encoding="utf-8")
    )
    user_step = strings["config"]["step"]["user"]
    assert "Allow insecure HTTP" in user_step["data"][CONF_ALLOW_INSECURE_HTTP]
    warning = user_step["data_description"][CONF_ALLOW_INSECURE_HTTP]
    assert "Warning" in warning
    assert "cleartext HTTP" in warning
    assert "insecure_http_required" in strings["config"]["error"]


async def test_user_flow_invalid_auth(hass) -> None:
    """Test that HTTP 401 surfaces as invalid_auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    with patch(
        "custom_components.plum_ecovent.config_flow.PlumEconetApi.async_get_sys_params",
        new=AsyncMock(side_effect=PlumEconetAuthError("nope")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=_user_input(allow_insecure_http=True),
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass) -> None:
    """Test that connection failures surface as cannot_connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    with patch(
        "custom_components.plum_ecovent.config_flow.PlumEconetApi.async_get_sys_params",
        new=AsyncMock(side_effect=PlumEconetConnectionError("timeout")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=_user_input(allow_insecure_http=True),
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_second_user_flow_aborts(hass, sys_params) -> None:
    """Test that Plum ecoVENT can only be configured once."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    with (
        patch(
            "custom_components.plum_ecovent.config_flow.PlumEconetApi.async_get_sys_params",
            new=AsyncMock(return_value=sys_params),
        ),
        patch(
            "custom_components.plum_ecovent.async_setup_entry",
            return_value=True,
        ),
    ):
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=_user_input(allow_insecure_http=True),
        )
        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


def _reauth_entry(hass) -> MockConfigEntry:
    """Add a configured entry that requires replacement credentials."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ecoVENT",
        unique_id=TEST_UID,
        data=_user_input(allow_insecure_http=True),
    )
    entry.add_to_hass(hass)
    return entry


async def test_reauth_updates_credentials_and_reloads(hass, sys_params) -> None:
    """Test successful reauthentication updates the existing entry."""
    entry = _reauth_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
            "unique_id": entry.unique_id,
        },
        data=entry.data,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with (
        patch(
            "custom_components.plum_ecovent.config_flow.PlumEconetApi.async_get_sys_params",
            new=AsyncMock(return_value=sys_params),
        ),
        patch("custom_components.plum_ecovent.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "new-user",
                CONF_PASSWORD: "new-password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_USERNAME] == "new-user"
    assert entry.data[CONF_PASSWORD] == "new-password"
    assert entry.data[CONF_HOST] == TEST_HOST


async def test_reauth_legacy_entry_without_insecure_http_option(
    hass, sys_params
) -> None:
    """Test reauthentication defaults a missing insecure-HTTP option to false."""
    entry = _reauth_entry(hass)
    hass.config_entries.async_update_entry(
        entry,
        data={
            key: value
            for key, value in entry.data.items()
            if key != CONF_ALLOW_INSECURE_HTTP
        },
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
            "unique_id": entry.unique_id,
        },
        data=entry.data,
    )
    api = MagicMock()
    api.async_get_sys_params = AsyncMock(return_value=sys_params)

    with (
        patch(
            "custom_components.plum_ecovent.config_flow.PlumEconetApi",
            return_value=api,
        ) as api_cls,
        patch("custom_components.plum_ecovent.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "new-user",
                CONF_PASSWORD: "new-password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_USERNAME] == "new-user"
    assert entry.data[CONF_PASSWORD] == "new-password"
    assert CONF_ALLOW_INSECURE_HTTP not in entry.data
    assert api_cls.call_args.kwargs["allow_insecure_http"] is False


async def test_reauth_rejects_invalid_credentials(hass) -> None:
    """Test failed replacement credentials keep the reauth form open."""
    entry = _reauth_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
            "unique_id": entry.unique_id,
        },
        data=entry.data,
    )

    with patch(
        "custom_components.plum_ecovent.config_flow.PlumEconetApi.async_get_sys_params",
        new=AsyncMock(side_effect=PlumEconetAuthError("nope")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: "wrong-password",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
    assert entry.data[CONF_PASSWORD] == TEST_PASSWORD


async def test_reauth_rejects_different_device(hass, sys_params) -> None:
    """Test reauthentication cannot replace the configured module identity."""
    entry = _reauth_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
            "unique_id": entry.unique_id,
        },
        data=entry.data,
    )

    with patch(
        "custom_components.plum_ecovent.config_flow.PlumEconetApi.async_get_sys_params",
        new=AsyncMock(return_value={**sys_params, "uid": "different-device"}),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "new-user",
                CONF_PASSWORD: "new-password",
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert entry.data[CONF_PASSWORD] == TEST_PASSWORD
