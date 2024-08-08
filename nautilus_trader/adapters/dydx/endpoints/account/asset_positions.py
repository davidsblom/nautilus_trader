"""
Provide the Get AssetPositions HTTP endpoint.
"""

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEndpointType
from nautilus_trader.adapters.dydx.endpoints.endpoint import DYDXHttpEndpoint
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.schemas.account.asset_positions import DYDXAssetPositionsResponse
from nautilus_trader.core.nautilus_pyo3 import HttpMethod


class DYDXGetAssetPositionsGetParams(msgspec.Struct, omit_defaults=True, frozen=True):
    """
    Define the parameters for the Get Asset Positions endpoint.
    """

    address: str
    subaccountNumber: float


class DYDXGetAssetPositionsEndpoint(DYDXHttpEndpoint):
    """
    Provide the Get Asset Positions HTTP endpoint.
    """

    def __init__(
        self,
        client: DYDXHttpClient,
    ) -> None:
        """
        Construct a new get address HTTP endpoint.
        """
        url_path = "/assetPositions"
        super().__init__(
            client=client,
            endpoint_type=DYDXEndpointType.ACCOUNT,
            url_path=url_path,
        )
        self.http_method = HttpMethod.GET
        self._get_resp_decoder = msgspec.json.Decoder(DYDXAssetPositionsResponse)

    async def get(self, params: DYDXGetAssetPositionsGetParams) -> DYDXAssetPositionsResponse:
        """
        Call the endpoint to list the instruments.
        """
        raw = await self._method(self.http_method, params)
        return self._get_resp_decoder.decode(raw)
