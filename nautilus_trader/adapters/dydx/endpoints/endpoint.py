"""
Define the base class for `dYdX` endpoints.
"""

from typing import Any

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEndpointType
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.core.nautilus_pyo3 import HttpMethod


class DYDXHttpEndpoint:
    """
    Define the base class for `dYdX` endpoints.
    """

    def __init__(
        self,
        client: DYDXHttpClient,
        endpoint_type: DYDXEndpointType,
        url_path: str | None = None,
    ) -> None:
        """
        Construct the base class for `dYdX` endpoints.
        """
        self.client = client
        self.endpoint_type = endpoint_type
        self.url_path = url_path

        self.decoder = msgspec.json.Decoder()
        self.encoder = msgspec.json.Encoder()

        self._method_request: dict[DYDXEndpointType, Any] = {
            DYDXEndpointType.NONE: self.client.send_request,
            DYDXEndpointType.ACCOUNT: self.client.send_request,
        }

    async def _method(
        self,
        method_type: HttpMethod,
        params: Any | None = None,
        url_path: str | None = None,
    ) -> bytes:
        payload: dict = self.decoder.decode(self.encoder.encode(params))
        method_call = self._method_request[self.endpoint_type]
        raw: bytes = await method_call(
            http_method=method_type,
            url_path=url_path or self.url_path,
            payload=payload,
        )
        return raw
