"""
Provide the Get Address HTTP endpoint.
"""

import datetime

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEndpointType
from nautilus_trader.adapters.dydx.common.enums import DYDXMarketType
from nautilus_trader.adapters.dydx.endpoints.endpoint import DYDXHttpEndpoint
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.schemas.account.fills import DYDXFillsResponse
from nautilus_trader.core.nautilus_pyo3 import HttpMethod


class DYDXGetFillsGetParams(msgspec.Struct, omit_defaults=True, frozen=True):
    """
    Define the parameters for the sub account endpoint.
    """

    address: str
    subaccountNumber: float
    market: str | None = None
    marketType: DYDXMarketType | None = None
    limit: float | None = None
    createdBeforeOrAtHeight: float | None = None
    createdBeforeOrAt: datetime.datetime | None = None
    page: float | None = None


class DYDXGetFillsEndpoint(DYDXHttpEndpoint):
    """
    Provide the sub account HTTP endpoint.
    """

    def __init__(
        self,
        client: DYDXHttpClient,
    ) -> None:
        """
        Construct a new get address HTTP endpoint.
        """
        url_path = "/fills"
        super().__init__(
            client=client,
            endpoint_type=DYDXEndpointType.ACCOUNT,
            url_path=url_path,
        )
        self.http_method = HttpMethod.GET
        self._get_resp_decoder = msgspec.json.Decoder(DYDXFillsResponse)

    async def get(self, params: DYDXGetFillsGetParams) -> DYDXFillsResponse:
        """
        Call the endpoint to list the instruments.
        """
        raw = await self._method(self.http_method, params)
        return self._get_resp_decoder.decode(raw)
