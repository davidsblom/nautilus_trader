"""
Define websocket message of the dYdX venue.
"""

# ruff: noqa: N815

import datetime
from decimal import Decimal

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXFillType
from nautilus_trader.adapters.dydx.common.enums import DYDXLiquidity
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderSide
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderStatus
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderType
from nautilus_trader.adapters.dydx.common.enums import DYDXPerpetualPositionStatus
from nautilus_trader.adapters.dydx.common.enums import DYDXPositionSide
from nautilus_trader.adapters.dydx.common.enums import DYDXTimeInForce
from nautilus_trader.adapters.dydx.common.enums import DYDXTransferType
from nautilus_trader.adapters.dydx.schemas.account.address import DYDXSubaccount
from nautilus_trader.adapters.dydx.schemas.account.orders import DYDXOrderResponse
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import BookOrder
from nautilus_trader.model.data import OrderBookDelta
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.enums import BookAction
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import RecordFlag
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity


class DYDXCandle(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the candles data.
    """

    baseTokenVolume: str
    close: str
    high: str
    low: str
    open: str
    resolution: str
    startedAt: datetime.datetime
    startingOpenInterest: str
    ticker: str
    trades: float
    usdVolume: str

    def parse_to_bar(
        self,
        bar_type: BarType,
        price_precision: int,
        size_precision: int,
        ts_init: int,
    ) -> Bar:
        """
        Parse the kline message into a nautilus Bar.
        """
        open_price = Price(float(self.open), price_precision)
        high_price = Price(float(self.high), price_precision)
        low_price = Price(float(self.low), price_precision)
        close_price = Price(float(self.close), price_precision)
        avg_price = Decimal("0.25") * (open_price + high_price + low_price + close_price)
        volume = Decimal(self.usdVolume) / avg_price
        return Bar(
            bar_type=bar_type,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=Quantity(volume, size_precision),
            ts_event=dt_to_unix_nanos(self.startedAt),
            ts_init=ts_init,
        )


class DYDXWsCandlesChannelData(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the candles channel data message from dYdX.
    """

    channel: str
    connection_id: str
    contents: DYDXCandle
    id: str
    message_id: int
    type: str
    version: str


class DYDXWsCandlesMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the candles contents.
    """

    candles: list[DYDXCandle]


class DYDXWsCandlesSubscribedData(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the candles channel data message from dYdX.
    """

    id: str
    channel: str
    connection_id: str
    contents: DYDXWsCandlesMessageContents
    message_id: int
    type: str


class DYDXWsMessageGeneral(msgspec.Struct):
    """
    Define a general websocket message from dYdX.
    """

    type: str | None = None
    connection_id: str | None = None
    message_id: int | None = None
    channel: str | None = None
    id: str | None = None


class DYDXTrade(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define a trade tick.
    """

    id: str
    side: DYDXOrderSide
    size: str
    price: str
    createdAt: datetime.datetime
    type: DYDXOrderType
    createdAtHeight: str | None = None

    def parse_to_trade_tick(
        self,
        instrument_id: InstrumentId,
        price_precision: int,
        size_precision: int,
        ts_init: int,
    ) -> TradeTick:
        """
        Parse the trade message to a TradeTick.
        """
        aggressor_side_map = {
            DYDXOrderSide.SELL: AggressorSide.SELLER,
            DYDXOrderSide.BUY: AggressorSide.BUYER,
        }
        return TradeTick(
            instrument_id=instrument_id,
            price=Price(float(self.price), price_precision),
            size=Quantity(float(self.size), size_precision),
            aggressor_side=aggressor_side_map[self.side],
            trade_id=TradeId(self.id),
            ts_event=dt_to_unix_nanos(self.createdAt),
            ts_init=ts_init,
        )


class DYDXWsTradeMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the trade message contents struct.
    """

    trades: list[DYDXTrade]


class DYDXWsTradeChannelData(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define a trade websocket message.
    """

    type: str
    connection_id: str
    message_id: int
    channel: str
    id: str
    contents: DYDXWsTradeMessageContents
    version: str | None = None
    clobPairId: str | None = None


# Price level: the first string indicates the price, the second string indicates the size
class DYDXWsOrderbookMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the order book message contents.
    """

    bids: list[list[str]] | None = None
    asks: list[list[str]] | None = None


class DYDXWsOrderbookChannelData(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the order book messages.
    """

    type: str
    connection_id: str
    message_id: int
    channel: str
    id: str
    contents: DYDXWsOrderbookMessageContents
    clobPairId: str | None = None
    version: str | None = None

    def parse_to_deltas(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        instrument_id: InstrumentId,
        price_precision: int,
        size_precision: int,
        ts_event: int,
        ts_init: int,
    ) -> OrderBookDeltas:
        """
        Parse the order book message into OrderBookDeltas.
        """
        if self.contents.bids is None:
            self.contents.bids = []

        if self.contents.asks is None:
            self.contents.asks = []

        num_bids_raw = len(self.contents.bids)
        num_asks_raw = len(self.contents.asks)
        deltas: list[OrderBookDelta] = []

        for bid_id, bid in enumerate(self.contents.bids):
            flags = 0

            if bid_id == num_bids_raw - 1 and num_asks_raw == 0:
                # F_LAST, 1 << 7
                # Last message in the packet from the venue for a given `instrument_id`
                flags = RecordFlag.F_LAST

            size = Quantity(float(bid[1]), size_precision)
            action = BookAction.DELETE if size == 0 else BookAction.UPDATE
            delta = OrderBookDelta(
                instrument_id=instrument_id,
                action=action,
                order=BookOrder(
                    side=OrderSide.BUY,
                    price=Price(float(bid[0]), price_precision),
                    size=size,
                    order_id=0,
                ),
                flags=flags,
                sequence=0,
                ts_event=ts_event,
                ts_init=ts_init,
            )
            deltas.append(delta)

        for ask_id, ask in enumerate(self.contents.asks):
            flags = 0

            if ask_id == num_asks_raw - 1:
                # F_LAST, 1 << 7
                # Last message in the packet from the venue for a given `instrument_id`
                flags = RecordFlag.F_LAST

            size = Quantity(float(ask[1]), size_precision)
            action = BookAction.DELETE if size == 0 else BookAction.UPDATE
            delta = OrderBookDelta(
                instrument_id=instrument_id,
                action=action,
                order=BookOrder(
                    side=OrderSide.SELL,
                    price=Price(float(ask[0]), price_precision),
                    size=size,
                    order_id=0,
                ),
                flags=flags,
                sequence=0,
                ts_event=ts_event,
                ts_init=ts_init,
            )
            deltas.append(delta)

        return OrderBookDeltas(instrument_id=instrument_id, deltas=deltas)


class PriceLevel(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define an order book level.
    """

    price: str
    size: str


class DYDXWsOrderbookMessageSnapshotContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the order book message contents.
    """

    bids: list[PriceLevel] | None = None
    asks: list[PriceLevel] | None = None


class DYDXWsOrderbookSnapshotChannelData(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the order book snapshot messages.
    """

    type: str
    connection_id: str
    message_id: int
    channel: str
    id: str
    contents: DYDXWsOrderbookMessageSnapshotContents
    version: str | None = None

    def parse_to_snapshot(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        instrument_id: InstrumentId,
        price_precision: int,
        size_precision: int,
        ts_event: int,
        ts_init: int,
    ) -> OrderBookDeltas:
        """
        Parse the order book message into OrderBookDeltas.
        """
        deltas: list[OrderBookDelta] = []

        # Add initial clear
        clear = OrderBookDelta.clear(
            instrument_id=instrument_id,
            ts_event=ts_event,
            ts_init=ts_init,
            sequence=0,
        )
        deltas.append(clear)

        if self.contents.bids is None:
            self.contents.bids = []

        if self.contents.asks is None:
            self.contents.asks = []

        num_bids_raw = len(self.contents.bids)
        num_asks_raw = len(self.contents.asks)

        for bid_id, bid in enumerate(self.contents.bids):
            flags = 0

            if bid_id == num_bids_raw - 1 and num_asks_raw == 0:
                # F_LAST, 1 << 7
                # Last message in the packet from the venue for a given `instrument_id`
                flags = RecordFlag.F_LAST

            order = BookOrder(
                side=OrderSide.BUY,
                price=Price(float(bid.price), price_precision),
                size=Quantity(float(bid.size), size_precision),
                order_id=0,
            )

            delta = OrderBookDelta(
                instrument_id=instrument_id,
                action=BookAction.ADD,
                order=order,
                flags=flags,
                sequence=0,
                ts_event=ts_event,
                ts_init=ts_init,
            )

            deltas.append(delta)

        for ask_id, ask in enumerate(self.contents.asks):
            flags = 0

            if ask_id == num_asks_raw - 1:
                # F_LAST, 1 << 7
                # Last message in the packet from the venue for a given `instrument_id`
                flags = RecordFlag.F_LAST

            delta = OrderBookDelta(
                instrument_id=instrument_id,
                action=BookAction.ADD,
                order=BookOrder(
                    side=OrderSide.SELL,
                    price=Price(float(ask.price), price_precision),
                    size=Quantity(float(ask.size), size_precision),
                    order_id=0,
                ),
                flags=flags,
                sequence=0,
                ts_event=ts_event,
                ts_init=ts_init,
            )
            deltas.append(delta)

        return OrderBookDeltas(instrument_id=instrument_id, deltas=deltas)


class DYDXWsSubaccountsSubscribedContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the contents of the sub accounts subscribed message.
    """

    subaccount: DYDXSubaccount | None = None
    orders: list[DYDXOrderResponse] | None = None
    blockHeight: str | None = None


class DYDXWsSubaccountsSubscribed(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the schema for the subaccounts initial response message.

    This channel provides realtime information about orders, fills, transfers,
    perpetual positions, and perpetual assets for a subaccount.

    The initial response returns everything from the
    /v4/addresses/:address/subaccountNumber/:subaccountNumber, and
    /v4/orders?addresses=${address}&subaccountNumber=${subaccountNumber}&status=OPEN.

    """

    type: str
    connection_id: str
    message_id: int
    channel: str
    id: str
    contents: DYDXWsSubaccountsSubscribedContents


class DYDXWalletAddress(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define a wallet address object.
    """

    address: str
    subaccountNumber: float | None = None


class DYDXWsTransferSubaccountMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define a transfer subaccount message.
    """

    sender: DYDXWalletAddress
    recipient: DYDXWalletAddress
    symbol: str
    size: str
    type: DYDXTransferType
    createdAt: datetime.datetime
    createdAtHeight: str
    transactionHash: str


class DYDXWsFillEventId(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the event id object of a fill message.
    """

    data: list[int]
    type: str


class DYDXWsFillSubaccountMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define a fill update message.
    """

    id: str
    subaccountId: str
    side: DYDXOrderSide
    liquidity: DYDXLiquidity
    type: DYDXFillType
    clobPairId: str
    size: str
    price: str
    quoteAmount: str
    eventId: DYDXWsFillEventId
    transactionHash: str
    createdAt: datetime.datetime
    createdAtHeight: str
    ticker: str
    orderId: str | None = None


class DYDXWsOrderSubaccountMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define an order update message.
    """

    id: str
    side: DYDXOrderSide
    size: str
    ticker: str
    price: str
    type: DYDXOrderType
    timeInForce: DYDXTimeInForce
    postOnly: bool
    reduceOnly: bool
    status: DYDXOrderStatus
    orderFlags: str
    clientMetadata: str | None = None
    clobPairId: str | None = None
    clientId: str | None = None
    subaccountId: str | None = None
    totalFilled: str | None = None
    totalOptimisticFilled: str | None = None
    goodTilBlock: str | None = None
    goodTilBlockTime: str | None = None
    removalReason: str | None = None
    createdAtHeight: str | None = None
    triggerPrice: str | None = None
    updatedAt: datetime.datetime | None = None
    updatedAtHeight: str | None = None


class DYDXWsAssetPositionSubaccountMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define an asset position update message.
    """

    address: str
    subaccountNumber: float
    positionId: str
    assetId: str
    symbol: str
    side: DYDXPositionSide
    size: str


class DYDXWsPerpetualPositionSubaccountMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define a perpetual position update message.
    """

    address: str
    subaccountNumber: float
    positionId: str
    market: str
    side: DYDXPositionSide
    status: DYDXPerpetualPositionStatus
    size: str
    maxSize: str
    netFunding: str
    entryPrice: str
    sumOpen: str
    sumClose: str
    exitPrice: str | None = None
    realizedPnl: str | None = None
    unrealizedPnl: str | None = None


class DYDXWsSubaccountMessageContents(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the contents of a subaccount message.
    """

    perpetualPositions: list[DYDXWsPerpetualPositionSubaccountMessageContents] | None = None

    # Asset position updates on the subaccount
    assetPositions: list[DYDXWsAssetPositionSubaccountMessageContents] | None = None

    # Order updates on the subaccount
    orders: list[DYDXWsOrderSubaccountMessageContents] | None = None

    # Fills that occur on the subaccount
    fills: list[DYDXWsFillSubaccountMessageContents] | None = None

    # Transfers that occur on the subaccount
    transfers: list[DYDXWsTransferSubaccountMessageContents] | None = None


class DYDXWsSubaccountsChannelData(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the schema for subaccounts updates.

    Responses will contain any update to open orders, changes in account, changes in
    open positions, and/or transfers in a single message.

    """

    channel: str
    id: str
    contents: DYDXWsSubaccountMessageContents
    eventIndex: float | None = None
    clobPairId: str | None = None
    transactionIndex: float | None = None
    blockHeight: str | None = None
    connection_id: str | None = None
    message_id: int | None = None
    type: str | None = None
    version: str | None = None
