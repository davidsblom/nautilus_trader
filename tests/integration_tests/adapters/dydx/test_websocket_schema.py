"""
Unit tests for the websocket messages of dYdX.
"""

from pathlib import Path

import msgspec
import pytest

from nautilus_trader.adapters.dydx.common.enums import DYDXOrderType
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsCandlesChannelData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsCandlesSubscribedData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsMessageGeneral
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsOrderbookChannelData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsOrderbookSnapshotChannelData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsSubaccountsChannelData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsSubaccountsSubscribed
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsTradeChannelData
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarAggregation
from nautilus_trader.model.data import BarSpecification
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import BookOrder
from nautilus_trader.model.data import OrderBookDelta
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import AggregationSource
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.enums import BookAction
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.enums import RecordFlag
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity


@pytest.mark.parametrize(
    "file_path",
    [
        "tests/fixtures/adapters/dydx/websocket/connected.json",
        "tests/fixtures/adapters/dydx/websocket/unsubscribed.json",
        "tests/fixtures/adapters/dydx/websocket/v4_candles_channel_data.json",
        "tests/fixtures/adapters/dydx/websocket/v4_candles.json",
        "tests/fixtures/adapters/dydx/websocket/v4_orderbook_snapshot.json",
        "tests/fixtures/adapters/dydx/websocket/v4_orderbook.json",
        "tests/fixtures/adapters/dydx/websocket/v4_trades.json",
        "tests/fixtures/adapters/dydx/websocket/trade_deleveraged.json",
        "tests/fixtures/adapters/dydx/websocket/v4_accounts_subscribed.json",
        "tests/fixtures/adapters/dydx/websocket/v4_accounts_channel_data.json",
    ],
)
def test_general_messsage(file_path: str) -> None:
    """
    Test the general message parser.
    """
    # Prepare
    decoder = msgspec.json.Decoder(DYDXWsMessageGeneral)

    # Act
    with Path(file_path).open() as file_reader:
        msg = decoder.decode(file_reader.read())

    # Assert
    assert msg.type is not None


def test_account_subscribed_message() -> None:
    """
    Teest parsing the account subscribed message.
    """
    # Prepare
    decoder = msgspec.json.Decoder(DYDXWsSubaccountsSubscribed)

    # Act
    with Path(
        "tests/fixtures/adapters/dydx/websocket/v4_accounts_subscribed.json",
    ).open() as file_reader:
        msg = decoder.decode(file_reader.read())

    # Assert
    assert msg.channel == "v4_subaccounts"


def test_account_channel_data_msg() -> None:
    """
    Teest parsing the account channel data.
    """
    # Prepare
    decoder = msgspec.json.Decoder(DYDXWsSubaccountsChannelData)

    # Act
    with Path(
        "tests/fixtures/adapters/dydx/websocket/v4_accounts_channel_data.json",
    ).open() as file_reader:
        msg = decoder.decode(file_reader.read())

    # Assert
    assert msg.channel == "v4_subaccounts"
    assert msg.contents.orders is not None
    assert len(msg.contents.orders) == 1


def test_klines_subscribed_data(dydx_instrument_id: InstrumentId) -> None:
    """
    Test parsing a candle message.
    """
    # Prepare
    decoder = msgspec.json.Decoder(DYDXWsCandlesSubscribedData)
    expected_bar = Bar(
        bar_type=BarType(
            instrument_id=dydx_instrument_id,
            bar_spec=BarSpecification(
                step=1,
                aggregation=BarAggregation.MINUTE,
                price_type=PriceType.LAST,
            ),
            aggregation_source=AggregationSource.EXTERNAL,
        ),
        open=Price.from_str("3248.7"),
        high=Price.from_str("3248.8"),
        low=Price.from_str("3248.1"),
        close=Price.from_str("3248.1"),
        volume=Quantity.from_str("2.015"),
        ts_event=1722016620000000000,
        ts_init=0,
    )

    with Path("tests/fixtures/adapters/dydx/websocket/v4_candles.json").open() as file_reader:
        msg = decoder.decode(file_reader.read())

    # Act
    result = msg.contents.candles[0].parse_to_bar(
        bar_type=BarType(
            instrument_id=dydx_instrument_id,
            bar_spec=BarSpecification(
                step=1,
                aggregation=BarAggregation.MINUTE,
                price_type=PriceType.LAST,
            ),
            aggregation_source=AggregationSource.EXTERNAL,
        ),
        price_precision=1,
        size_precision=3,
        ts_init=0,
    )

    # Assert
    assert msg.channel == "v4_candles"
    assert result == expected_bar
    assert result.open == expected_bar.open
    assert result.high == expected_bar.high
    assert result.low == expected_bar.low
    assert result.close == expected_bar.close
    assert result.ts_event == expected_bar.ts_event
    assert result.ts_init == expected_bar.ts_init
    assert result.volume == expected_bar.volume


def test_klines_channel_data(dydx_instrument_id: InstrumentId) -> None:
    """
    Test parsing a candle message.
    """
    # Prepare
    decoder = msgspec.json.Decoder(DYDXWsCandlesChannelData)
    expected_bar = Bar(
        bar_type=BarType(
            instrument_id=dydx_instrument_id,
            bar_spec=BarSpecification(
                step=1,
                aggregation=BarAggregation.MINUTE,
                price_type=PriceType.LAST,
            ),
            aggregation_source=AggregationSource.EXTERNAL,
        ),
        open=Price.from_str("3246.5"),
        high=Price.from_str("3247.6"),
        low=Price.from_str("3246.5"),
        close=Price.from_str("3247.6"),
        volume=Quantity.from_str("6.364"),
        ts_event=1722016440000000000,
        ts_init=0,
    )

    with Path(
        "tests/fixtures/adapters/dydx/websocket/v4_candles_channel_data.json",
    ).open() as file_reader:
        msg = decoder.decode(file_reader.read())

    # Act
    result = msg.contents.parse_to_bar(
        bar_type=BarType(
            instrument_id=dydx_instrument_id,
            bar_spec=BarSpecification(
                step=1,
                aggregation=BarAggregation.MINUTE,
                price_type=PriceType.LAST,
            ),
            aggregation_source=AggregationSource.EXTERNAL,
        ),
        price_precision=1,
        size_precision=3,
        ts_init=0,
    )

    # Assert
    assert msg.channel == "v4_candles"
    assert msg.connection_id == "8c25ab80-2124-4f60-82bf-9040cabc03af"
    assert result == expected_bar
    assert result.open == expected_bar.open
    assert result.high == expected_bar.high
    assert result.low == expected_bar.low
    assert result.close == expected_bar.close
    assert result.ts_event == expected_bar.ts_event
    assert result.ts_init == expected_bar.ts_init
    assert result.volume == expected_bar.volume


def test_orderbook(dydx_instrument_id: InstrumentId) -> None:
    """
    Test parsing the orderbook.
    """
    # Prepare
    expected_num_deltas = 1
    decoder = msgspec.json.Decoder(DYDXWsOrderbookChannelData)

    with Path("tests/fixtures/adapters/dydx/websocket/v4_orderbook.json").open() as file_reader:
        msg = decoder.decode(file_reader.read())

    # Act
    deltas = msg.parse_to_deltas(
        instrument_id=dydx_instrument_id,
        price_precision=0,
        size_precision=5,
        ts_event=0,
        ts_init=0,
    )

    # Assert
    assert len(deltas.deltas) == expected_num_deltas
    assert deltas.deltas[0].order.size == 0
    assert deltas.deltas[0].action == BookAction.DELETE

    for delta_id, delta in enumerate(deltas.deltas):
        if delta_id < len(deltas.deltas) - 1:
            assert delta.flags == 0
        else:
            assert delta.flags == RecordFlag.F_LAST


def test_orderbook_snapshot(dydx_instrument_id: InstrumentId) -> None:
    """
    Test parsing the orderbook snapshot.
    """
    # Prepare
    expected_num_deltas = 201
    expected_clear = OrderBookDelta.clear(
        instrument_id=dydx_instrument_id,
        ts_event=0,
        ts_init=0,
        sequence=0,
    )
    expected_delta = OrderBookDelta(
        instrument_id=dydx_instrument_id,
        action=BookAction.ADD,
        order=BookOrder(
            side=OrderSide.BUY,
            price=Price(3393.2, 1),
            size=Quantity(7.795, 3),
            order_id=0,
        ),
        flags=0,
        sequence=0,
        ts_event=0,
        ts_init=0,
    )
    decoder = msgspec.json.Decoder(DYDXWsOrderbookSnapshotChannelData)

    with Path(
        "tests/fixtures/adapters/dydx/websocket/v4_orderbook_snapshot.json",
    ).open() as file_reader:
        msg = decoder.decode(file_reader.read())

    # Act
    deltas = msg.parse_to_snapshot(
        instrument_id=dydx_instrument_id,
        price_precision=1,
        size_precision=3,
        ts_event=0,
        ts_init=0,
    )

    # Assert
    assert len(deltas.deltas) == expected_num_deltas
    assert deltas.deltas[0] == expected_clear
    assert deltas.deltas[1] == expected_delta
    assert deltas.deltas[1].order.price == expected_delta.order.price
    assert deltas.deltas[1].order.size == expected_delta.order.size
    assert deltas.deltas[1].order.side == expected_delta.order.side

    for delta_id, delta in enumerate(deltas.deltas):
        if delta_id < len(deltas.deltas) - 1:
            assert delta.flags == 0
        else:
            assert delta.flags == RecordFlag.F_LAST


def test_trades(dydx_instrument_id: InstrumentId) -> None:
    """
    Test parsing trade messages.
    """
    # Prepare
    expected_num_trades = 2
    expected_trade = TradeTick(
        instrument_id=dydx_instrument_id,
        price=Price(3393, 0),
        size=Quantity(0.01, 5),
        aggressor_side=AggressorSide.BUYER,
        trade_id=TradeId("014206cf0000000200000002"),
        ts_event=1721848355705000000,
        ts_init=0,
    )
    decoder = msgspec.json.Decoder(DYDXWsTradeChannelData)

    # Act
    with Path("tests/fixtures/adapters/dydx/websocket/v4_trades.json").open() as file_reader:
        msg = decoder.decode(file_reader.read())

    trade_tick = msg.contents.trades[0].parse_to_trade_tick(
        instrument_id=dydx_instrument_id,
        price_precision=0,
        size_precision=5,
        ts_init=0,
    )

    # Assert
    assert len(msg.contents.trades) == expected_num_trades
    assert trade_tick == expected_trade
    assert trade_tick.instrument_id == expected_trade.instrument_id
    assert trade_tick.price == expected_trade.price
    assert trade_tick.size == expected_trade.size
    assert trade_tick.aggressor_side == expected_trade.aggressor_side
    assert trade_tick.trade_id == expected_trade.trade_id
    assert trade_tick.ts_event == expected_trade.ts_event
    assert trade_tick.ts_init == expected_trade.ts_init


def test_trades_deleveraged(dydx_instrument_id: InstrumentId) -> None:
    """
    Test parsing trade messages.
    """
    # Prepare
    expected_num_trades = 3
    expected_trade = TradeTick(
        instrument_id=dydx_instrument_id,
        price=Price(2340.7442700369913687, 0),
        size=Quantity(0.811, 5),
        aggressor_side=AggressorSide.SELLER,
        trade_id=TradeId("015034b90000000200000026"),
        ts_event=1722820168338000000,
        ts_init=0,
    )
    decoder = msgspec.json.Decoder(DYDXWsTradeChannelData)

    # Act
    with Path(
        "tests/fixtures/adapters/dydx/websocket/trade_deleveraged.json",
    ).open() as file_reader:
        msg = decoder.decode(file_reader.read())

    trade_tick = msg.contents.trades[2].parse_to_trade_tick(
        instrument_id=dydx_instrument_id,
        price_precision=0,
        size_precision=5,
        ts_init=0,
    )

    # Assert
    assert msg.contents.trades[2].type == DYDXOrderType.DELEVERAGED
    assert len(msg.contents.trades) == expected_num_trades
    assert trade_tick.instrument_id == expected_trade.instrument_id
    assert trade_tick.price == expected_trade.price
    assert trade_tick.size == expected_trade.size
    assert trade_tick.aggressor_side == expected_trade.aggressor_side
    assert trade_tick.trade_id == expected_trade.trade_id
    assert trade_tick.ts_event == expected_trade.ts_event
    assert trade_tick.ts_init == expected_trade.ts_init
    assert trade_tick == expected_trade
