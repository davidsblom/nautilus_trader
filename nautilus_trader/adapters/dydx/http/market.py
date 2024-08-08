"""
Define the `dYdX` API for calling market endpoints.
"""

from nautilus_trader.adapters.dydx.endpoints.market.instruments_info import DYDXListPerpetualMarketsEndpoint
from nautilus_trader.adapters.dydx.endpoints.market.instruments_info import DYDXListPerpetualMarketsResponse
from nautilus_trader.adapters.dydx.endpoints.market.instruments_info import ListPerpetualMarketsGetParams
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.common.component import LiveClock
from nautilus_trader.core.correctness import PyCondition


class DYDXMarketHttpAPI:
    """
    Define the `dYdX` API for calling market endpoints.
    """

    def __init__(
        self,
        client: DYDXHttpClient,
        clock: LiveClock,
    ) -> None:
        """
        Define the `dYdX` API for calling market endpoints.
        """
        PyCondition.not_none(client, "client")
        self.client = client
        self._clock = clock

        self._endpoint_instruments = DYDXListPerpetualMarketsEndpoint(client)

    async def fetch_instruments(
        self,
        symbol: str | None = None,
        limit: float | None = None,
    ) -> DYDXListPerpetualMarketsResponse:
        """
        Fetch all the instruments for the `dYdX` venue.
        """
        return await self._endpoint_instruments.get(
            ListPerpetualMarketsGetParams(ticker=symbol, limit=limit),
        )
