"""
Read the authentication secrets from environment variables.
"""

from nautilus_trader.adapters.env import get_env_key


def get_wallet_address(is_testnet: bool) -> str:
    """
    Return the API key for dYdX.
    """
    if is_testnet:
        key = get_env_key("DYDX_TESTNET_WALLET_ADDRESS")

        if not key:
            message = "DYDX_TESTNET_WALLET_ADDRESS environment variable not set"
            raise ValueError(message)

        return key

    key = get_env_key("DYDX_WALLET_ADDRESS")

    if not key:
        message = "DYDX_WALLET_ADDRESS environment variable not set"
        raise ValueError(message)

    return key
