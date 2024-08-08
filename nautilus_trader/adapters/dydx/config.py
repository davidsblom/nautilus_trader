"""
Define the dYdX configuration classes.
"""

from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt


class DYDXDataClientConfig(LiveDataClientConfig, frozen=True):
    """
    Configuration for ``DYDXDataClient`` instances.

    testnet : bool, default False
        If the client is connecting to the dYdX testnet API.

    """

    testnet: bool = False


class DYDXExecClientConfig(LiveExecClientConfig, frozen=True):
    """
    Configuration for ``BybitExecutionClient`` instances.

    testnet : bool, default False
        If the client is connecting to the Bybit testnet API.
    use_gtd : bool, default False
        If False then GTD time in force will be remapped to GTC
        (this is useful if managing GTD orders locally).

    """

    wallet_address: str | None = None
    subaccount: float = 0
    base_url_http: str | None = None
    base_url_ws: str | None = None
    testnet: bool = False
    use_gtd: bool = False
    use_reduce_only: bool = True
    use_position_ids: bool = True
    treat_expired_as_canceled: bool = False
    max_retries: PositiveInt | None = None
    retry_delay: PositiveFloat | None = None
