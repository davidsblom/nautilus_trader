"""
Create fixtures for commonly used objects.
"""

import pytest

from nautilus_trader.adapters.dydx.common.symbol import DYDXSymbol
from nautilus_trader.model.identifiers import InstrumentId


@pytest.fixture()
def dydx_symbol() -> DYDXSymbol:
    """
    Create a stub symbol.
    """
    return DYDXSymbol("BTC-USD")


@pytest.fixture()
def dydx_instrument_id() -> InstrumentId:
    """
    Create a stub instrument id.
    """
    return InstrumentId.from_str("BTC-USD-PERP.DYDX")
