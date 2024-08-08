"""
Provide the Get Address HTTP endpoint.
"""

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEndpointType
from nautilus_trader.adapters.dydx.endpoints.endpoint import DYDXHttpEndpoint
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.schemas.account.orders import DYDXOrderResponse
from nautilus_trader.core.nautilus_pyo3 import HttpMethod


class DYDXGetOrderGetParams(msgspec.Struct, omit_defaults=True, frozen=True):
    """
    Define the parameters for the order endpoint.
    """

    address: str
    subaccountNumber: float


class DYDXGetOrderEndpoint(DYDXHttpEndpoint):
    """
    Provide the orders HTTP endpoint.
    """

    def __init__(
        self,
        client: DYDXHttpClient,
    ) -> None:
        """
        Construct a new get address HTTP endpoint.
        """
        url_path = "/orders"
        super().__init__(
            client=client,
            endpoint_type=DYDXEndpointType.ACCOUNT,
            url_path=url_path,
        )
        self.http_method = HttpMethod.GET
        self._get_resp_decoder = msgspec.json.Decoder(DYDXOrderResponse)

    async def get(self, order_id: str, params: DYDXGetOrderGetParams) -> DYDXOrderResponse:
        """
        Call the endpoint to list the instruments.
        """
        url_path = f"/orders/{order_id}"
        raw = await self._method(self.http_method, params, url_path=url_path)
        return self._get_resp_decoder.decode(raw)
