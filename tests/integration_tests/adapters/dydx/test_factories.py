"""
Unit tests for the dYdX factories.
"""

import asyncio

import pytest

from nautilus_trader.adapters.dydx.common.urls import get_http_base_url
from nautilus_trader.adapters.dydx.common.urls import get_ws_base_url_public
from nautilus_trader.adapters.dydx.config import DYDXDataClientConfig
from nautilus_trader.adapters.dydx.data import DYDXDataClient
from nautilus_trader.adapters.dydx.factories import DYDXLiveDataClientFactory
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.test_kit.mocks.cache_database import MockCacheDatabase


@pytest.mark.parametrize(
    ("is_testnet", "expected"),
    [
        (False, "https://indexer.dydx.trade/v4"),
        (True, "https://indexer.v4testnet.dydx.exchange/v4"),
    ],
)
def test_get_http_base_url(is_testnet: bool, expected: str) -> None:
    """
    Test the base url for the http endpoints.
    """
    base_url = get_http_base_url(is_testnet)
    assert base_url == expected


@pytest.mark.parametrize(
    ("is_testnet", "expected"),
    [
        (False, "wss://indexer.dydx.trade/v4/ws"),
        (True, "wss://indexer.v4testnet.dydx.exchange/v4/ws"),
    ],
)
def test_get_ws_base_url(is_testnet: bool, expected: str) -> None:
    """
    Test the base url for the websocket endpoints.
    """
    base_url = get_ws_base_url_public(is_testnet)
    assert base_url == expected


def test_create_bybit_live_data_client() -> None:
    """
    Test the data client factory for dYdX.
    """
    # Prepare
    clock = LiveClock()
    msgbus = MessageBus(
        trader_id=TraderId("TESTER-000"),
        clock=clock,
    )
    cache = Cache(database=MockCacheDatabase())

    # Act
    data_client = DYDXLiveDataClientFactory.create(
        loop=asyncio.get_event_loop(),
        name="DYDX",
        config=DYDXDataClientConfig(),
        msgbus=msgbus,
        cache=cache,
        clock=clock,
    )

    # Assert
    assert isinstance(data_client, DYDXDataClient)
