"""
Provides a `DYDX` asynchronous HTTP client.
"""

import asyncio
import random
import urllib
from typing import Any

import msgspec

import nautilus_trader
from nautilus_trader.adapters.dydx.http.errors import DYDXError
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.nautilus_pyo3 import HttpClient
from nautilus_trader.core.nautilus_pyo3 import HttpMethod
from nautilus_trader.core.nautilus_pyo3 import HttpResponse
from nautilus_trader.core.nautilus_pyo3 import Quota


INTERNAL_SERVER_ERROR_CODE = 500
BAD_REQUEST_ERROR_CODE = 400


class DYDXHttpClient:
    """
    Provide a `DYDX` asynchronous HTTP client.

    Parameters
    ----------
    clock : LiveClock
        The clock for the client.
    base_url : str, optional
        The base endpoint URL for the client.
    ratelimiter_quotas : list[tuple[str, Quota]], optional
        The keyed rate limiter quotas for the client.
    ratelimiter_quota : Quota, optional
        The default rate limiter quota for the client.

    """

    def __init__(
        self,
        clock: LiveClock,
        base_url: str,
        ratelimiter_quotas: list[tuple[str, Quota]] | None = None,
        ratelimiter_default_quota: Quota | None = None,
    ) -> None:
        """
        Provide a `dYdX` asynchronous HTTP client.
        """
        self._clock: LiveClock = clock
        self._log: Logger = Logger(type(self).__name__)
        self._base_url: str = base_url
        self._headers: dict[str, Any] = {
            "Content-Type": "application/json",
            "User-Agent": nautilus_trader.USER_AGENT,
        }
        self._client = HttpClient(
            keyed_quotas=ratelimiter_quotas or [],
            default_quota=ratelimiter_default_quota,
        )

    @property
    def base_url(self) -> str:
        """
        Return the base URL being used by the client.

        Returns
        -------
        str

        """
        return self._base_url

    @property
    def headers(self) -> dict[str, Any]:
        """
        Return the headers being used by the client.

        Returns
        -------
        str

        """
        return self._headers

    async def send_request(
        self,
        http_method: HttpMethod,
        url_path: str,
        payload: dict[str, str] | None = None,
        ratelimiter_keys: list[str] | None = None,
        max_tries: int = 5,
        sleep_duration_secs: float = 1.0,
        max_sleep_secs: int = 30,
    ) -> bytes | None:
        """
        Asynchronously send an HTTP request.
        """
        if payload:
            url_path += "?" + urllib.parse.urlencode(payload)
            payload = None  # Don't send payload in the body

        self._log.debug(f"{self._base_url + url_path} {payload}", LogColor.MAGENTA)
        done = False

        for retry_counter in range(max_tries):
            if not done:
                try:
                    response: HttpResponse = await self._client.request(
                        http_method,
                        url=self._base_url + url_path,
                        headers=self._headers,
                        body=msgspec.json.encode(payload) if payload else None,
                        keys=ratelimiter_keys,
                        timeout_secs=10,
                    )
                    done = True
                except Exception as e:
                    if retry_counter < max_tries - 1:
                        self._log.warning(
                            f"Failed to perform HTTP request: {e}. Retry {retry_counter + 1}/{max_tries}. Sleep {sleep_duration_secs:0.1f}s",
                        )
                        await asyncio.sleep(sleep_duration_secs)
                        random_multiplier = random.uniform(1.8, 2.2)  # noqa: S311
                        sleep_duration_secs = min(
                            sleep_duration_secs * random_multiplier,
                            max_sleep_secs,
                        )
                    else:
                        self._log.error(f"Failed to perform HTTP request: {e}")
                        raise

        if BAD_REQUEST_ERROR_CODE <= response.status < INTERNAL_SERVER_ERROR_CODE:
            raise DYDXError(
                status=response.status,
                message=msgspec.json.decode(response.body) if response.body else None,
                headers=response.headers,
            )

        if response.status >= INTERNAL_SERVER_ERROR_CODE:
            raise DYDXError(
                status=response.status,
                message=msgspec.json.decode(response.body) if response.body else None,
                headers=response.headers,
            )

        return response.body
