"""
Define the account HTTP API endpoints.
"""

from nautilus_trader.adapters.dydx.endpoints.account.address import DYDXGetAddressEndpoint
from nautilus_trader.adapters.dydx.endpoints.account.address import DYDXGetAddressGetParams
from nautilus_trader.adapters.dydx.endpoints.account.asset_positions import DYDXGetAssetPositionsEndpoint
from nautilus_trader.adapters.dydx.endpoints.account.asset_positions import DYDXGetAssetPositionsGetParams
from nautilus_trader.adapters.dydx.endpoints.account.fills import DYDXGetFillsEndpoint
from nautilus_trader.adapters.dydx.endpoints.account.fills import DYDXGetFillsGetParams
from nautilus_trader.adapters.dydx.endpoints.account.order import DYDXGetOrderEndpoint
from nautilus_trader.adapters.dydx.endpoints.account.order import DYDXGetOrderGetParams
from nautilus_trader.adapters.dydx.endpoints.account.orders import DYDXGetOrdersEndpoint
from nautilus_trader.adapters.dydx.endpoints.account.orders import DYDXGetOrdersGetParams
from nautilus_trader.adapters.dydx.endpoints.account.perpetual_positions import DYDXGetPerpetualPositionsEndpoint
from nautilus_trader.adapters.dydx.endpoints.account.perpetual_positions import DYDXGetPerpetualPositionsGetParams
from nautilus_trader.adapters.dydx.endpoints.account.subaccount import DYDXGetSubaccountEndpoint
from nautilus_trader.adapters.dydx.endpoints.account.subaccount import DYDXGetSubaccountGetParams
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.schemas.account.address import DYDXAddressResponse
from nautilus_trader.adapters.dydx.schemas.account.address import DYDXSubaccountResponse
from nautilus_trader.adapters.dydx.schemas.account.asset_positions import DYDXAssetPositionsResponse
from nautilus_trader.adapters.dydx.schemas.account.fills import DYDXFillsResponse
from nautilus_trader.adapters.dydx.schemas.account.orders import DYDXOrderResponse
from nautilus_trader.adapters.dydx.schemas.account.perpetual_positions import DYDXPerpetualPositionsResponse
from nautilus_trader.common.component import LiveClock
from nautilus_trader.core.correctness import PyCondition


class DYDXAccountHttpAPI:
    """
    Define the account HTTP API endpoints.
    """

    def __init__(
        self,
        client: DYDXHttpClient,
        clock: LiveClock,
    ) -> None:
        """
        Define the account HTTP API endpoints.
        """
        PyCondition.not_none(client, "client")
        self.client = client
        self._clock = clock

        self._endpoint_get_address = DYDXGetAddressEndpoint(client)
        self._endpoint_get_subaccount = DYDXGetSubaccountEndpoint(client)
        self._endpoint_get_asset_positions = DYDXGetAssetPositionsEndpoint(client)
        self._endpoint_get_perpetual_positions = DYDXGetPerpetualPositionsEndpoint(client)
        self._endpoint_get_orders = DYDXGetOrdersEndpoint(client)
        self._endpoint_get_order = DYDXGetOrderEndpoint(client)
        self._endpoint_get_fills = DYDXGetFillsEndpoint(client)

    async def get_adress_subaccounts(self, address: str) -> DYDXAddressResponse:
        """
        Fetch the address subaccounts.
        """
        return await self._endpoint_get_address.get(DYDXGetAddressGetParams(address=address))

    async def get_subaccount(
        self,
        address: str,
        subaccount_number: float,
    ) -> DYDXSubaccountResponse:
        """
        Fetch the subaccount.
        """
        return await self._endpoint_get_subaccount.get(
            DYDXGetSubaccountGetParams(
                address=address,
                subaccountNumber=subaccount_number,
            ),
        )

    async def get_asset_positions(
        self,
        address: str,
        subaccount_number: float,
    ) -> DYDXAssetPositionsResponse:
        """
        Fetch the asset positions.
        """
        return await self._endpoint_get_asset_positions.get(
            DYDXGetAssetPositionsGetParams(
                address=address,
                subaccountNumber=subaccount_number,
            ),
        )

    async def get_perpetual_positions(
        self,
        address: str,
        subaccount_number: float,
    ) -> DYDXPerpetualPositionsResponse:
        """
        Fetch the perpetual positions.
        """
        return await self._endpoint_get_perpetual_positions.get(
            DYDXGetPerpetualPositionsGetParams(
                address=address,
                subaccountNumber=subaccount_number,
            ),
        )

    async def get_orders(self, address: str, subaccount_number: float) -> list[DYDXOrderResponse]:
        """
        Fetch the orders.
        """
        return await self._endpoint_get_orders.get(
            DYDXGetOrdersGetParams(
                address=address,
                subaccountNumber=subaccount_number,
            ),
        )

    async def get_order(
        self,
        address: str,
        subaccount_number: float,
        order_id: str,
    ) -> DYDXOrderResponse:
        """
        Fetch a specific order.
        """
        return await self._endpoint_get_order.get(
            order_id=order_id,
            params=DYDXGetOrderGetParams(
                address=address,
                subaccountNumber=subaccount_number,
            ),
        )

    async def get_fills(self, address: str, subaccount_number: float) -> DYDXFillsResponse:
        """
        Fetch the fills.
        """
        return await self._endpoint_get_fills.get(
            DYDXGetFillsGetParams(
                address=address,
                subaccountNumber=subaccount_number,
            ),
        )
