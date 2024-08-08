"""
Provide factories to construct data and execution clients for dYdX.
"""

import asyncio

from nautilus_trader.adapters.dydx.common.urls import get_http_base_url
from nautilus_trader.adapters.dydx.common.urls import get_ws_base_url_public
from nautilus_trader.adapters.dydx.config import DYDXDataClientConfig
from nautilus_trader.adapters.dydx.config import DYDXExecClientConfig
from nautilus_trader.adapters.dydx.data import DYDXDataClient
from nautilus_trader.adapters.dydx.execution import DYDXExecutionClient
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.providers import DYDXInstrumentProvider
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.live.factories import LiveDataClientFactory
from nautilus_trader.live.factories import LiveExecClientFactory


HTTP_CLIENTS: dict[str, DYDXHttpClient] = {}


def get_dydx_http_client(
    clock: LiveClock,
    base_url: str | None = None,
    is_testnet: bool = False,
) -> DYDXHttpClient:
    """
    Cache and return a Bybit HTTP client with the given key and secret.

    If a cached client with matching key and secret already exists, then that cached
    client will be returned.

    Parameters
    ----------
    clock : LiveClock
        The clock for the client.
    base_url : str, optional
        The base URL for the API endpoints.
    is_testnet : bool, default False
        If the client is connecting to the testnet API.

    Returns
    -------
    DYDXHttpClient

    """
    http_base_url = base_url or get_http_base_url(is_testnet)

    if http_base_url not in HTTP_CLIENTS:
        client = DYDXHttpClient(
            clock=clock,
            base_url=http_base_url,
        )
        HTTP_CLIENTS[http_base_url] = client

    return HTTP_CLIENTS[http_base_url]


def get_dydx_instrument_provider(
    client: DYDXHttpClient,
    clock: LiveClock,
    config: InstrumentProviderConfig,
) -> DYDXInstrumentProvider:
    """
    Cache and return a dYdX instrument provider.

    If a cached provider with matching key and secret already exists, then that
    cached provider will be returned.

    Parameters
    ----------
    client : BybitHttpClient
        The client for the instrument provider.
    clock : LiveClock
        The clock for the instrument provider.
    config : InstrumentProviderConfig
        The configuration for the instrument provider.

    Returns
    -------
    DYDXInstrumentProvider

    """
    return DYDXInstrumentProvider(client=client, config=config, clock=clock)


class DYDXLiveDataClientFactory(LiveDataClientFactory):
    """
    Provides a `Bybit` live data client factory.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: DYDXDataClientConfig,  # type: ignore[override]
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> DYDXDataClient:
        """
        Create a new dYdX data client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop for the client.
        name : str
            The custom client ID.
        config : DYDXDataClientConfig
            The client configuration.
        msgbus : MessageBus
            The message bus for the client.
        cache : Cache
            The cache for the client.
        clock: LiveClock
            The clock for the instrument provider.

        Returns
        -------
        DYDXDataClient

        """
        client: DYDXHttpClient = get_dydx_http_client(
            clock=clock,
            is_testnet=config.testnet,
        )
        provider = get_dydx_instrument_provider(
            client=client,
            clock=clock,
            config=config.instrument_provider,
        )
        ws_base_url = get_ws_base_url_public(is_testnet=config.testnet)
        return DYDXDataClient(
            loop=loop,
            client=client,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            ws_base_url=ws_base_url,
            config=config,
            name=name,
        )


class DYDXLiveExecClientFactory(LiveExecClientFactory):
    """
    Provides a `dYdX` live execution client factory.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: DYDXExecClientConfig,  # type: ignore[override]
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> DYDXExecutionClient:
        """
        Create a new dYdX execution client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop for the client.
        name : str
            The custom client ID.
        config : DYDXExecClientConfig
            The client configuration.
        msgbus : MessageBus
            The message bus for the client.
        cache : Cache
            The cache for the client.
        clock : LiveClock
            The clock for the client.

        Returns
        -------
        DYDXExecutionClient

        """
        client: DYDXHttpClient = get_dydx_http_client(
            clock=clock,
            base_url=config.base_url_http,
            is_testnet=config.testnet,
        )
        provider = get_dydx_instrument_provider(
            client=client,
            clock=clock,
            config=config.instrument_provider,
        )
        ws_base_url = get_ws_base_url_public(is_testnet=config.testnet)
        return DYDXExecutionClient(
            loop=loop,
            client=client,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            base_url_ws=config.base_url_ws or ws_base_url,
            config=config,
            name=name,
        )
