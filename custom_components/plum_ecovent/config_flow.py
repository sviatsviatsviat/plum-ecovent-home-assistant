"""Config flow for Plum ecoVENT."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PlumEconetApi
from .const import CONF_ALLOW_INSECURE_HTTP, DOMAIN, NAME
from .exceptions import (
    PlumEconetAuthError,
    PlumEconetConnectionError,
    PlumEconetError,
    PlumEconetInsecureHttpError,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_ALLOW_INSECURE_HTTP, default=False): bool,
    }
)


class PlumEconetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Plum ecoVENT."""

    VERSION = 1

    async def _async_validate(
        self, data: Mapping[str, Any]
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Validate credentials and return sysParams or a form error."""
        session = async_get_clientsession(self.hass)
        try:
            api = PlumEconetApi(
                session,
                data[CONF_HOST],
                data[CONF_USERNAME],
                data[CONF_PASSWORD],
                allow_insecure_http=bool(
                    data.get(CONF_ALLOW_INSECURE_HTTP, False)
                ),
            )
            return await api.async_get_sys_params(), None
        except PlumEconetInsecureHttpError:
            return None, "insecure_http_required"
        except PlumEconetAuthError:
            return None, "invalid_auth"
        except PlumEconetConnectionError:
            return None, "cannot_connect"
        except PlumEconetError:
            return None, "unknown"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            allow_insecure_http = bool(user_input[CONF_ALLOW_INSECURE_HTTP])
            sys_params, error = await self._async_validate(user_input)
            if error is not None:
                errors["base"] = error
            elif sys_params is not None:
                uid = sys_params.get("uid")
                if not uid:
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(str(uid))
                    self._abort_if_unique_id_configured()
                    title = str(sys_params.get("controllerID") or NAME)
                    return self.async_create_entry(
                        title=title,
                        data={
                            CONF_HOST: user_input[CONF_HOST].strip(),
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_ALLOW_INSECURE_HTTP: allow_insecure_http,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Start reauthentication for an existing config entry."""
        self._reauth_data = dict(entry_data)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate replacement credentials and reload the config entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = {
                **self._reauth_data,
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }
            sys_params, error = await self._async_validate(candidate)
            if error is not None:
                errors["base"] = error
            elif sys_params is None or not (uid := sys_params.get("uid")):
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(uid))
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=self._reauth_data[CONF_USERNAME],
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
