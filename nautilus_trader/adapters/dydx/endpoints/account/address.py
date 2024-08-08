"""
Provide the Get Address HTTP endpoint.
"""

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEndpointType
from nautilus_trader.adapters.dydx.endpoints.endpoint import DYDXHttpEndpoint
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.schemas.account.address import DYDXAddressResponse
from nautilus_trader.core.nautilus_pyo3 import HttpMethod


class DYDXGetAddressGetParams(msgspec.Struct, omit_defaults=True, frozen=True):
    """
    Define the parameters for the Get Address endpoint.
    """

    address: str


class DYDXGetAddressEndpoint(DYDXHttpEndpoint):
    """
    Provide the Get Address HTTP endpoint.
    """

    def __init__(
        self,
        client: DYDXHttpClient,
    ) -> None:
        """
        Construct a new get address HTTP endpoint.
        """
        super().__init__(
            client=client,
            endpoint_type=DYDXEndpointType.ACCOUNT,
        )
        self.http_method = HttpMethod.GET
        self._get_resp_decoder = msgspec.json.Decoder(DYDXAddressResponse)

    async def get(self, params: DYDXGetAddressGetParams) -> DYDXAddressResponse:
        """
        Call the endpoint to list the instruments.
        """
        url_path = f"/addresses/{params.address}"
        raw = await self._method(self.http_method, params=None, url_path=url_path)
        return self._get_resp_decoder.decode(raw)
