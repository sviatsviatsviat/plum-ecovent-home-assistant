"""Local ecoNET300 HTTP client.

Adapted from the Basic-auth HTTP call pattern in bulgur/plum-econet
(https://gitlab.com/bulgur/plum-econet), Copyright (c) 2022 Paweł Tomak,
MIT License. Retargeted for ecoVENT modules using sysParams, regParams,
editParams, and newParam (not remote-menu / rm* endpoints).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urljoin, urlparse

import aiohttp
from aiohttp import ClientError, ClientTimeout, encode_basic_auth, hdrs

from .const import (
    API_PATH_EDIT_PARAMS,
    API_PATH_NEW_PARAM,
    API_PATH_REG_PARAMS,
    API_PATH_SYS_PARAMS,
)
from .exceptions import (
    PlumEconetAuthError,
    PlumEconetConnectionError,
    PlumEconetInsecureHttpError,
)

_DEFAULT_TIMEOUT = ClientTimeout(total=15)


def _resolve_host(host: str, *, allow_insecure_http: bool) -> str:
    """Normalize host and enforce the insecure-HTTP opt-in."""
    resolved = host.strip().rstrip("/")
    if "://" not in resolved:
        if not allow_insecure_http:
            raise PlumEconetInsecureHttpError(
                "Host-only addresses use cleartext HTTP; enable allow insecure "
                "HTTP explicitly, or provide an https:// URL."
            )
        resolved = f"http://{resolved}"

    scheme = urlparse(resolved).scheme.lower()
    if scheme == "http":
        if not allow_insecure_http:
            raise PlumEconetInsecureHttpError(
                "Cleartext HTTP requires an explicit allow insecure HTTP opt-in."
            )
    elif scheme != "https":
        raise PlumEconetConnectionError(
            f"Unsupported URL scheme {scheme!r}; use http:// or https://"
        )
    return resolved


class PlumEconetApi:
    """Async HTTP client for a local ecoNET300 module."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        username: str,
        password: str,
        *,
        allow_insecure_http: bool = False,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._host = _resolve_host(host, allow_insecure_http=allow_insecure_http)
        self._username = username
        self._allow_insecure_http = allow_insecure_http
        try:
            # aiohttp 3.14 deprecates BasicAuth in favor of this RFC 7617 helper.
            self._auth_header = {
                hdrs.AUTHORIZATION: encode_basic_auth(username, password)
            }
        except ValueError as err:
            raise PlumEconetConnectionError(
                "Invalid HTTP Basic authentication username"
            ) from err
        self._base = f"{self._host}/econet/"

    @property
    def _auth_permitted(self) -> bool:
        """Return whether Basic auth may be sent for the resolved transport."""
        scheme = urlparse(self._host).scheme.lower()
        if scheme == "https":
            return True
        return scheme == "http" and self._allow_insecure_http

    def __repr__(self) -> str:
        """Return a representation that omits the password."""
        return (
            f"{self.__class__.__name__}(host={self._host!r}, "
            f"username={self._username!r})"
        )

    async def _call_api(self, cmd: str) -> Any:
        """GET /econet/{cmd} with HTTP Basic auth and return JSON."""
        url = urljoin(self._base, cmd)
        try:
            async with self._session.get(
                url,
                headers=self._auth_header if self._auth_permitted else {},
                timeout=_DEFAULT_TIMEOUT,
                allow_redirects=False,
            ) as resp:
                if 300 <= resp.status < 400:
                    location = resp.headers.get(hdrs.LOCATION)
                    destination = urljoin(url, location) if location else None
                    if destination and urlparse(destination).scheme.lower() == "http":
                        raise PlumEconetConnectionError(
                            f"Refusing cleartext HTTP redirect to {destination}"
                        )
                    raise PlumEconetConnectionError(
                        f"Got {resp.status} {resp.reason} when calling {url}"
                    )
                if resp.status == 401:
                    raise PlumEconetAuthError("Invalid credentials")
                if resp.status != 200:
                    raise PlumEconetConnectionError(
                        f"Got {resp.status} {resp.reason} when calling {url}"
                    )
                return await resp.json(content_type=None)
        except TimeoutError as err:
            raise PlumEconetConnectionError(f"Timeout calling {url}") from err
        except ClientError as err:
            raise PlumEconetConnectionError(f"Error calling {url}: {err}") from err
        except ValueError as err:
            raise PlumEconetConnectionError(
                f"Invalid JSON response when calling {url}"
            ) from err

    async def async_get_sys_params(self) -> dict[str, Any]:
        """Fetch device identity and polling hints (sysParams)."""
        data = await self._call_api(API_PATH_SYS_PARAMS)
        if not isinstance(data, dict):
            raise PlumEconetConnectionError("sysParams response was not an object")
        return data

    async def async_get_reg_params(self) -> dict[str, Any]:
        """Fetch live register parameters (regParams)."""
        data = await self._call_api(API_PATH_REG_PARAMS)
        if not isinstance(data, dict):
            raise PlumEconetConnectionError("regParams response was not an object")
        return data

    async def async_get_edit_params(self) -> dict[str, Any]:
        """Fetch editable parameter registry (editParams)."""
        data = await self._call_api(API_PATH_EDIT_PARAMS)
        if not isinstance(data, dict):
            raise PlumEconetConnectionError("editParams response was not an object")
        return data

    async def async_set_param(self, name: str, value: Any) -> dict[str, Any]:
        """Write a parameter via newParam.

        Prefer the numeric parameter id as ``name`` (e.g. ``\"17\"`` for
        ``REKWS1``); string names are unverified on this module.

        Success requires a JSON object with ``result == \"OK\"`` (LAN shape:
        ``paramName`` / ``paramValue`` / ``result``). Any other body is failure.
        """
        cmd = (
            f"{API_PATH_NEW_PARAM}?newParamName={quote(str(name), safe='')}"
            f"&newParamValue={quote(str(value), safe='')}"
        )
        data = await self._call_api(cmd)
        if not isinstance(data, dict) or data.get("result") != "OK":
            raise PlumEconetConnectionError(
                f"newParam write failed for {name}={value}: {data!r}"
            )
        return data
