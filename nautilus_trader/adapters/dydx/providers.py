"""
Instrument provider for the dYdX venue.
"""

from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.http.market import DYDXMarketHttpAPI
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.model.identifiers import InstrumentId


class DYDXInstrumentProvider(InstrumentProvider):
    """
    Instrument provider for the dYdX venue.

    Provides a way to load instruments from dYdX.

    Parameters
    ----------
    client : DYDXHttpClient
        The dYdX HTTP client.
    clock : LiveClock
        The clock instance.

    """

    def __init__(
        self,
        client: DYDXHttpClient,
        clock: LiveClock,
        config: InstrumentProviderConfig | None = None,
    ) -> None:
        """
        Provide a way to load instruments from dYdX.
        """
        super().__init__(config=config)
        self._clock = clock
        self._client = client

        self._http_market = DYDXMarketHttpAPI(client=client, clock=clock)

    async def load_all_async(self, filters: dict | None = None) -> None:
        """
        Load all instruments asynchronously, optionally applying filters.
        """
        filters_str = "..." if not filters else f" with filters {filters}..."
        self._log.info(f"Loading all instruments{filters_str}")

        await self._load_instruments()

        self._log.info(f"Loaded {len(self._instruments)} instruments")

    async def load_ids_async(
        self,
        instrument_ids: list[InstrumentId],
        filters: dict | None = None,
    ) -> None:
        """
        Load specific instruments by their IDs.
        """
        message = "method `load_ids_async` must be implemented in the subclass"
        raise NotImplementedError(message)

    async def load_async(
        self,
        instrument_id: InstrumentId,
        filters: dict | None = None,
    ) -> None:
        """
        Load a single instrument by its ID.
        """
        message = "method `load_async` must be implemented in the subclass"
        raise NotImplementedError(message)

    async def _load_instruments(self) -> None:
        markets = await self._http_market.fetch_instruments()

        for market in markets.markets.values():
            try:
                base_currency = market.parse_base_currency()
                quote_currency = market.parse_quote_currency()
                ts_event = self._clock.timestamp_ns()
                ts_init = self._clock.timestamp_ns()
                instrument = market.parse_to_instrument(
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    ts_event=ts_event,
                    ts_init=ts_init,
                )
                self.add_currency(base_currency)
                self.add_currency(quote_currency)
                self.add(instrument)
            except ValueError as e:
                self._log.warning(f"Unable to parse linear instrument {market.ticker}: {e}")
