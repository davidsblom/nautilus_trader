"""
Define base urls for HTTP endpoints and websocket data streams.
"""


def get_http_base_url(is_testnet: bool) -> str:
    """
    Provide the base HTTP url for dYdX.
    """
    if is_testnet:
        return "https://indexer.v4testnet.dydx.exchange/v4"

    return "https://indexer.dydx.trade/v4"


def get_ws_base_url_public(is_testnet: bool) -> str:
    """
    Provide the base websockets url for dYdX.
    """
    return "wss://indexer.dydx.trade/v4/ws"
    if is_testnet:
        return "wss://indexer.v4testnet.dydx.exchange/v4/ws"

    return "wss://indexer.dydx.trade/v4/ws"
