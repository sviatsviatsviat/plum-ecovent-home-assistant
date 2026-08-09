"""The Plum ecoVENT integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PlumEconetApi
from .const import (
    CONF_ALLOW_INSECURE_HTTP,
    DEFAULT_MODEL,
    DOMAIN,
    MANUFACTURER,
    NAME,
)
from .coordinator import PlumEconetCoordinator
from .exceptions import PlumEconetInsecureHttpError

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR]

type PlumEconetConfigEntry = ConfigEntry[PlumEconetCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PlumEconetConfigEntry) -> bool:
    """Set up Plum ecoVENT from a config entry."""
    host = entry.data.get(CONF_HOST)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    if not host or username is None or password is None:
        raise ConfigEntryError(
            "This Plum ecoVENT entry is missing host credentials. "
            "Remove it and add the integration again with the module IP, "
            "username, and password."
        )

    session = async_get_clientsession(hass)
    allow_insecure_http = bool(entry.data.get(CONF_ALLOW_INSECURE_HTTP, False))
    try:
        api = PlumEconetApi(
            session,
            host,
            username,
            password,
            allow_insecure_http=allow_insecure_http,
        )
    except PlumEconetInsecureHttpError as err:
        raise ConfigEntryError(
            "Cleartext HTTP requires enabling Allow insecure HTTP. "
            "Remove this entry and add the integration again with that "
            "option enabled."
        ) from err
    coordinator = PlumEconetCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    sys_params = coordinator.sys_params
    uid = str(sys_params["uid"])

    entry.runtime_data = coordinator
    # Keep polling while no platforms/entities have registered listeners yet.
    entry.async_on_unload(coordinator.async_add_listener(lambda: None))

    model = sys_params.get("controllerID") or DEFAULT_MODEL
    sw_version = sys_params.get("softVer") or sys_params.get("moduleASoftVer")

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, uid)},
        manufacturer=MANUFACTURER,
        model=str(model),
        name=NAME,
        sw_version=str(sw_version) if sw_version else None,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PlumEconetConfigEntry) -> bool:
    """Unload a Plum ecoVENT config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and hasattr(entry, "runtime_data"):
        object.__delattr__(entry, "runtime_data")
    return unload_ok
