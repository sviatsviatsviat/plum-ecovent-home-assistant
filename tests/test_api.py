"""Tests for the Plum ecoVENT API client."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError, encode_basic_auth, hdrs

from custom_components.plum_ecovent.api import PlumEconetApi
from custom_components.plum_ecovent.exceptions import (
    PlumEconetAuthError,
    PlumEconetConnectionError,
    PlumEconetInsecureHttpError,
)


def _mock_response(
    status: int,
    payload: object | None = None,
    *,
    headers: dict[str, str] | None = None,
) -> MagicMock:
    """Build an async context-manager response mock."""
    response = MagicMock()
    response.status = status
    response.reason = "Error" if status != 200 else "OK"
    response.headers = headers or {}
    response.json = AsyncMock(return_value=payload if payload is not None else {})
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


def _api(
    session: MagicMock,
    host: str = "192.0.2.10",
    *,
    allow_insecure_http: bool = True,
) -> PlumEconetApi:
    """Build an API client for tests."""
    return PlumEconetApi(
        session,
        host,
        "user",
        "pass",
        allow_insecure_http=allow_insecure_http,
    )


async def test_get_sys_params_success() -> None:
    """Test successful sysParams fetch."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, {"uid": "ABC"}))
    api = _api(session)

    result = await api.async_get_sys_params()

    assert result == {"uid": "ABC"}
    session.get.assert_called_once()
    assert "sysParams" in session.get.call_args.args[0]
    assert session.get.call_args.kwargs["allow_redirects"] is False
    assert session.get.call_args.kwargs["headers"][hdrs.AUTHORIZATION] == (
        encode_basic_auth("user", "pass")
    )


async def test_host_only_requires_insecure_http_opt_in() -> None:
    """Test that host-only input does not silently enable HTTP."""
    session = MagicMock()

    with pytest.raises(PlumEconetInsecureHttpError):
        _api(session, "192.0.2.10", allow_insecure_http=False)

    session.get.assert_not_called()


async def test_explicit_http_requires_insecure_http_opt_in() -> None:
    """Test that an http:// URL is rejected without the opt-in."""
    session = MagicMock()

    with pytest.raises(PlumEconetInsecureHttpError):
        _api(session, "http://192.0.2.10", allow_insecure_http=False)

    session.get.assert_not_called()


async def test_host_only_with_opt_in_uses_http_and_auth() -> None:
    """Test that opt-in derives http:// and sends Basic Authorization."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, {"uid": "ABC"}))
    api = _api(session, "192.0.2.10", allow_insecure_http=True)

    await api.async_get_sys_params()

    url = session.get.call_args.args[0]
    assert url.startswith("http://192.0.2.10/econet/")
    assert session.get.call_args.kwargs["headers"][hdrs.AUTHORIZATION] == (
        encode_basic_auth("user", "pass")
    )


async def test_https_without_opt_in_sends_auth() -> None:
    """Test that https:// is permitted without the insecure-HTTP opt-in."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, {"uid": "ABC"}))
    api = _api(session, "https://192.0.2.10", allow_insecure_http=False)

    await api.async_get_sys_params()

    url = session.get.call_args.args[0]
    assert url.startswith("https://192.0.2.10/econet/")
    assert session.get.call_args.kwargs["headers"][hdrs.AUTHORIZATION] == (
        encode_basic_auth("user", "pass")
    )


async def test_get_sys_params_invalid_json() -> None:
    """Test malformed successful responses become connection errors."""
    session = MagicMock()
    response = _mock_response(200)
    response.json = AsyncMock(side_effect=ValueError("invalid JSON"))
    session.get = MagicMock(return_value=response)
    api = _api(session)

    with pytest.raises(PlumEconetConnectionError, match="Invalid JSON response"):
        await api.async_get_sys_params()


async def test_basic_auth_rejects_colon_in_username() -> None:
    """Test invalid Basic-auth usernames are reported as connection errors."""
    with pytest.raises(
        PlumEconetConnectionError, match="Invalid HTTP Basic authentication"
    ):
        PlumEconetApi(
            MagicMock(),
            "192.0.2.10",
            "invalid:user",
            "pass",
            allow_insecure_http=True,
        )


async def test_rejects_cleartext_http_redirect() -> None:
    """Test that redirects to http:// fail before a follow-up request."""
    session = MagicMock()
    session.get = MagicMock(
        return_value=_mock_response(
            302,
            headers={hdrs.LOCATION: "http://192.0.2.99/econet/sysParams"},
        )
    )
    api = _api(session)

    with pytest.raises(PlumEconetConnectionError, match="Refusing cleartext HTTP redirect"):
        await api.async_get_sys_params()

    session.get.assert_called_once()
    assert session.get.call_args.kwargs["allow_redirects"] is False


async def test_set_param_rejects_cleartext_http_redirect() -> None:
    """Test that async_set_param uses the same redirect policy."""
    session = MagicMock()
    session.get = MagicMock(
        return_value=_mock_response(
            301,
            headers={hdrs.LOCATION: "http://evil.example/steal"},
        )
    )
    api = _api(session, "http://192.0.2.10")

    with pytest.raises(PlumEconetConnectionError, match="Refusing cleartext HTTP redirect"):
        await api.async_set_param("17", 3)

    session.get.assert_called_once()
    assert session.get.call_args.kwargs["allow_redirects"] is False


async def test_get_sys_params_unauthorized() -> None:
    """Test that HTTP 401 raises PlumEconetAuthError."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(401))
    api = _api(session)

    with pytest.raises(PlumEconetAuthError):
        await api.async_get_sys_params()


async def test_get_sys_params_http_error() -> None:
    """Test that non-200 responses raise PlumEconetConnectionError."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(500))
    api = _api(session)

    with pytest.raises(PlumEconetConnectionError):
        await api.async_get_sys_params()


async def test_get_sys_params_timeout() -> None:
    """Test that timeouts raise PlumEconetConnectionError."""
    session = MagicMock()
    session.get = MagicMock(side_effect=TimeoutError())
    api = _api(session)

    with pytest.raises(PlumEconetConnectionError):
        await api.async_get_sys_params()


async def test_get_sys_params_client_error() -> None:
    """Test that aiohttp client errors raise PlumEconetConnectionError."""
    session = MagicMock()
    session.get = MagicMock(side_effect=ClientError())
    api = _api(session)

    with pytest.raises(PlumEconetConnectionError):
        await api.async_get_sys_params()


async def test_repr_omits_password() -> None:
    """Test that __repr__ does not include the password."""
    session = MagicMock()
    api = PlumEconetApi(
        session,
        "192.0.2.10",
        "user",
        "super-secret",
        allow_insecure_http=True,
    )

    text = repr(api)

    assert "super-secret" not in text
    assert "user" in text
    assert "192.0.2.10" in text


async def test_set_param_builds_new_param_query() -> None:
    """Test that writes use newParamName / newParamValue with numeric id."""
    session = MagicMock()
    session.get = MagicMock(
        return_value=_mock_response(
            200, {"paramName": "17", "paramValue": 3, "result": "OK"}
        )
    )
    api = _api(session, "http://192.0.2.10")

    result = await api.async_set_param("17", 3)

    assert result == {"paramName": "17", "paramValue": 3, "result": "OK"}
    url = session.get.call_args.args[0]
    assert "newParam?" in url
    assert "newParamName=17" in url
    assert "newParamValue=3" in url
    assert "rmNewParam" not in url


async def test_set_param_rejects_non_ok_result() -> None:
    """Test that a non-OK newParam body raises PlumEconetConnectionError."""
    session = MagicMock()
    session.get = MagicMock(
        return_value=_mock_response(200, {"paramName": "17", "result": "ERROR"})
    )
    api = _api(session, "http://192.0.2.10")

    with pytest.raises(PlumEconetConnectionError, match="newParam write failed"):
        await api.async_set_param("17", 3)


async def test_set_param_rejects_non_object_body() -> None:
    """Test that a non-object newParam body raises PlumEconetConnectionError."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, ["OK"]))
    api = _api(session, "http://192.0.2.10")

    with pytest.raises(PlumEconetConnectionError, match="newParam write failed"):
        await api.async_set_param("20", 2)
