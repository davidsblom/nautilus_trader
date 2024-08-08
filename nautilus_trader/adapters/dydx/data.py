"""
Provide a data client for the `dYdX` decentralized cypto exchange.
"""

import asyncio
from typing import Any

import msgspec

from nautilus_trader.adapters.dydx.common.constants import DYDX_VENUE
from nautilus_trader.adapters.dydx.common.parsing import get_interval_from_bar_type
from nautilus_trader.adapters.dydx.common.symbol import DYDXSymbol
from nautilus_trader.adapters.dydx.config import DYDXDataClientConfig
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.providers import DYDXInstrumentProvider
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsCandlesChannelData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsCandlesSubscribedData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsMessageGeneral
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsOrderbookChannelData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsOrderbookSnapshotChannelData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsTradeChannelData
from nautilus_trader.adapters.dydx.websocket.client import DYDXWebsocketClient
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.live.data_client import LiveMarketDataClient
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId


class DYDXDataClient(LiveMarketDataClient):
    """
    Provide a data client for the `dYdX` decentralized cypto exchange.

    Parameters
    ----------
    loop : asyncio.AbstractEventLoop
        The event loop for the client.
    client : DYDXHttpClient
        The dYdX HTTP client.
    msgbus : MessageBus
        The message bus for the client.
    cache : Cache
        The cache for the client.
    clock : LiveClock
        The clock for the client.
    instrument_provider : DYDXInstrumentProvider
        The instrument provider.
    ws_base_url: str
        The product base url for the WebSocket client.
    config : DYDXDataClientConfig
        The configuration for the client.
    name : str, optional
        The custom client ID.

    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client: DYDXHttpClient,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        instrument_provider: DYDXInstrumentProvider,
        ws_base_url: str,
        config: DYDXDataClientConfig,
        name: str | None,
    ) -> None:
        """
        Provide a data client for the `dYdX` decentralized cypto exchange.
        """
        super().__init__(
            loop=loop,
            client_id=ClientId(name or DYDX_VENUE.value),
            venue=DYDX_VENUE,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=instrument_provider,
        )

        self._decoder_ws_msg_general = msgspec.json.Decoder(DYDXWsMessageGeneral)
        self._decoder_ws_orderbook = msgspec.json.Decoder(DYDXWsOrderbookChannelData)
        self._decoder_ws_orderbook_snapshot = msgspec.json.Decoder(
            DYDXWsOrderbookSnapshotChannelData,
        )
        self._decoder_ws_trade = msgspec.json.Decoder(DYDXWsTradeChannelData)
        self._decoder_ws_kline = msgspec.json.Decoder(DYDXWsCandlesChannelData)
        self._decoder_ws_kline_subscribed = msgspec.json.Decoder(DYDXWsCandlesSubscribedData)
        self._ws_client = DYDXWebsocketClient(
            clock=clock,
            handler=self._handle_ws_message,
            base_url=ws_base_url,
            loop=loop,
        )

        self._topic_bar_type: dict[str, BarType] = {}

        self._update_instrument_interval: int = 60 * 60  # Once per hour (hardcode)
        self._update_instruments_task: asyncio.Task | None = None

    async def _connect(self) -> None:
        self._log.info("Initializing instruments...")
        await self._instrument_provider.initialize()

        self._send_all_instruments_to_data_engine()
        self._update_instruments_task = self.create_task(self._update_instruments())

        self._log.info("Initializing websocket connection")
        await self._ws_client.connect()

        self._log.info("Data client connected")

    async def _disconnect(self) -> None:
        if self._update_instruments_task:
            self._log.debug("Cancelling `update_instruments` task")
            self._update_instruments_task.cancel()
            self._update_instruments_task = None

        await self._ws_client.disconnect()

        self._log.info("Data client disconnected")

    async def _update_instruments(self) -> None:
        try:
            while True:
                self._log.debug(
                    f"Scheduled `update_instruments` to run in {self._update_instrument_interval}s",
                )
                await asyncio.sleep(self._update_instrument_interval)
                await self._instrument_provider.load_all_async()
                self._send_all_instruments_to_data_engine()
        except asyncio.CancelledError:
            self._log.debug("Canceled `update_instruments` task")

    def _send_all_instruments_to_data_engine(self) -> None:
        for instrument in self._instrument_provider.get_all().values():
            self._handle_data(instrument)

        for currency in self._instrument_provider.currencies().values():
            self._cache.add_currency(currency)

    def _handle_ws_message(self, raw: bytes) -> None:
        try:
            ws_message = self._decoder_ws_msg_general.decode(raw)

            if ws_message.channel == "v4_orderbook" and ws_message.type == "channel_data":
                self._handle_orderbook(raw)
            elif ws_message.channel == "v4_trades" and ws_message.type in (
                "channel_data",
                "subscribed",
            ):
                self._handle_trade(raw)
            elif ws_message.channel == "v4_candles" and ws_message.type == "channel_data":
                self._handle_kline(raw)
            elif ws_message.channel == "v4_orderbook" and ws_message.type == "subscribed":
                self._handle_orderbook_snapshot(raw)
            elif ws_message.channel == "v4_candles" and ws_message.type == "subscribed":
                self._handle_kline_subscribed(raw)
            elif ws_message.type == "unsubscribed":
                self._log.info(
                    f"Unsubscribed from channel {ws_message.channel} for {ws_message.id}",
                )

                if ws_message.channel == "v4_candles":
                    self._handle_kline_unsubscribed(ws_message)
            elif ws_message.type == "connected":
                self._log.info("Websocket connected")
            else:
                self._log.error(f"Unknown message `{ws_message.type}`: {raw.decode()}")
        except Exception as e:
            self._log.error(f"Failed to parse websocket message: {raw.decode()} with error {e}")

    def _handle_trade(self, raw: bytes) -> None:
        try:
            msg: DYDXWsTradeChannelData = self._decoder_ws_trade.decode(raw)
            symbol = msg.id
            instrument_id: InstrumentId = self._get_cached_instrument_id(symbol)

            instrument = self._cache.instrument(instrument_id)

            if instrument is None:
                self._log.error(f"Cannot parse trade data: no instrument for {instrument_id}")
                return

            for tick_msg in msg.contents.trades:
                trade_tick = tick_msg.parse_to_trade_tick(
                    instrument_id,
                    price_precision=instrument.price_precision,
                    size_precision=instrument.size_precision,
                    ts_init=self._clock.timestamp_ns(),
                )
                self._handle_data(trade_tick)

        except Exception as e:
            self._log.error(f"Failed to parse trade tick: {raw.decode()} with error {e}")

    def _handle_orderbook(self, raw: bytes) -> None:
        try:
            msg: DYDXWsOrderbookChannelData = self._decoder_ws_orderbook.decode(raw)

            symbol = msg.id
            instrument_id: InstrumentId = self._get_cached_instrument_id(symbol)

            instrument = self._cache.instrument(instrument_id)

            if instrument is None:
                self._log.error(f"Cannot parse orderbook data: no instrument for {instrument_id}")
                return

            deltas = msg.parse_to_deltas(
                instrument_id=instrument_id,
                price_precision=instrument.price_precision,
                size_precision=instrument.size_precision,
                ts_event=self._clock.timestamp_ns(),
                ts_init=self._clock.timestamp_ns(),
            )
            self._handle_data(deltas)

        except Exception as e:
            self._log.error(f"Failed to parse orderbook: {raw.decode()} with error {e}")

    def _handle_orderbook_snapshot(self, raw: bytes) -> None:
        try:
            msg: DYDXWsOrderbookSnapshotChannelData = self._decoder_ws_orderbook_snapshot.decode(
                raw,
            )

            symbol = msg.id
            instrument_id: InstrumentId = self._get_cached_instrument_id(symbol)

            instrument = self._cache.instrument(instrument_id)

            if instrument is None:
                self._log.error(
                    f"Cannot parse orderbook snapshot: no instrument for {instrument_id}",
                )
                return

            deltas = msg.parse_to_snapshot(
                instrument_id=instrument_id,
                price_precision=instrument.price_precision,
                size_precision=instrument.size_precision,
                ts_event=self._clock.timestamp_ns(),
                ts_init=self._clock.timestamp_ns(),
            )
            self._handle_data(deltas)

        except Exception as e:
            self._log.error(f"Failed to parse orderbook snapshot: {raw.decode()} with error {e}")

    def _handle_kline(self, raw: bytes) -> None:
        try:
            msg: DYDXWsCandlesChannelData = self._decoder_ws_kline.decode(raw)

            symbol = msg.contents.ticker
            instrument_id: InstrumentId = self._get_cached_instrument_id(symbol)

            instrument = self._cache.instrument(instrument_id)

            if instrument is None:
                self._log.error(f"Cannot parse kline data: no instrument for {instrument_id}")
                return

            bar_type = self._topic_bar_type.get(msg.id)

            if bar_type is None:
                self._log.error(f"Cannot parse kline data: no bar type for {instrument_id}")
                return

            parsed_bar = msg.contents.parse_to_bar(
                bar_type=bar_type,
                price_precision=instrument.price_precision,
                size_precision=instrument.size_precision,
                ts_init=self._clock.timestamp_ns(),
            )
            self._handle_data(parsed_bar)

        except Exception as e:
            self._log.error(f"Failed to parse kline data: {raw.decode()} with error {e}")

    def _handle_kline_subscribed(self, raw: bytes) -> None:
        try:
            msg: DYDXWsCandlesSubscribedData = self._decoder_ws_kline_subscribed.decode(raw)

            symbol = msg.id.split("/")[0]
            instrument_id: InstrumentId = self._get_cached_instrument_id(symbol)

            instrument = self._cache.instrument(instrument_id)

            if instrument is None:
                self._log.error(f"Cannot parse bar: no instrument for {instrument_id}")
                return

            bar_type = self._topic_bar_type.get(msg.id)

            if bar_type is None:
                self._log.error(f"Cannot parse kline data: no bar type for {instrument_id}")
                return

            for candle in msg.contents.candles:
                parsed_bar = candle.parse_to_bar(
                    bar_type=bar_type,
                    price_precision=instrument.price_precision,
                    size_precision=instrument.size_precision,
                    ts_init=self._clock.timestamp_ns(),
                )
                self._handle_data(parsed_bar)

        except Exception as e:
            self._log.error(f"Failed to parse bar: {raw.decode()} with error {e}")

    def _handle_kline_unsubscribed(self, msg: DYDXWsMessageGeneral) -> None:
        if msg.id is not None:
            self._topic_bar_type.pop(msg.id, None)

    async def _subscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        dydx_symbol = DYDXSymbol(instrument_id.symbol.value)
        await self._ws_client.subscribe_trades(dydx_symbol.raw_symbol)

    async def _subscribe_order_book_deltas(
        self,
        instrument_id: InstrumentId,
        book_type: BookType,
        depth: int | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        if book_type in (BookType.L1_MBP, BookType.L3_MBO):
            self._log.error(
                "Cannot subscribe to order book deltas: L3_MBO data is not published by dYdX. The only valid book type is L2_MBP",
            )
            return

        dydx_symbol = DYDXSymbol(instrument_id.symbol.value)
        await self._ws_client.subscribe_order_book(dydx_symbol.raw_symbol)

    async def _subscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        self._log.error("Cannot subscribe to quotes: quote ticks are not published by dYdX.")

    async def _subscribe_bars(self, bar_type: BarType) -> None:
        self._log.info(f"Subscribe to {bar_type} bars")
        dydx_symbol = DYDXSymbol(bar_type.instrument_id.symbol.value)
        candles_resolution = get_interval_from_bar_type(bar_type)
        topic = f"{dydx_symbol.raw_symbol}/{candles_resolution.value}"
        self._topic_bar_type[topic] = bar_type
        await self._ws_client.subscribe_klines(dydx_symbol.raw_symbol, candles_resolution)

    async def _unsubscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        dydx_symbol = DYDXSymbol(instrument_id.symbol.value)
        await self._ws_client.unsubscribe_trades(dydx_symbol.raw_symbol)

    async def _unsubscribe_order_book_deltas(self, instrument_id: InstrumentId) -> None:
        dydx_symbol = DYDXSymbol(instrument_id.symbol.value)
        await self._ws_client.unsubscribe_order_book(dydx_symbol.raw_symbol)

    async def _unsubscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        self._log.error("Cannot unsubscribe from quotes: quote ticks are not published by dYdX.")

    async def _unsubscribe_bars(self, bar_type: BarType) -> None:
        dydx_symbol = DYDXSymbol(bar_type.instrument_id.symbol.value)
        candles_resolution = get_interval_from_bar_type(bar_type)
        await self._ws_client.unsubscribe_klines(dydx_symbol.raw_symbol, candles_resolution)

    def _get_cached_instrument_id(self, symbol: str) -> InstrumentId:
        dydx_symbol = DYDXSymbol(symbol)
        nautilus_instrument_id: InstrumentId = dydx_symbol.parse_as_nautilus()
        return nautilus_instrument_id
