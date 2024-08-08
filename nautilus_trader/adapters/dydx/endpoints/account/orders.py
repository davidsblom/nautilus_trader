"""
Provide the Get Address HTTP endpoint.
"""

import datetime

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEndpointType
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderSide
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderStatus
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderType
from nautilus_trader.adapters.dydx.endpoints.endpoint import DYDXHttpEndpoint
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.schemas.account.orders import DYDXOrderResponse
from nautilus_trader.core.nautilus_pyo3 import HttpMethod


class DYDXGetOrdersGetParams(msgspec.Struct, omit_defaults=True, frozen=True):
    """
    Define the parameters for the order endpoint.
    """

    address: str
    subaccountNumber: float
    limit: float | None = None
    ticker: str | None = None
    side: DYDXOrderSide | None = None
    type: DYDXOrderType | None = None
    status: list[DYDXOrderStatus] | None = None
    goodTilBlockBeforeOrAt: float | None = None
    goodTilBlockTimeBeforeOrAt: datetime.datetime | None = None
    returnLatestOrders: bool | None = None


class DYDXGetOrdersEndpoint(DYDXHttpEndpoint):
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

    async def get(self, params: DYDXGetOrdersGetParams) -> list[DYDXOrderResponse]:
        """
        Call the endpoint to list the instruments.
        """
        raw = await self._method(self.http_method, params)
        return msgspec.json.decode(raw, type=list[DYDXOrderResponse], strict=True)
