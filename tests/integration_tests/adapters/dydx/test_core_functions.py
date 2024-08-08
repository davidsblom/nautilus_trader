"""
Unit tests for core functions.
"""

from nautilus_trader.adapters.dydx.common.constants import DYDX_VENUE
from nautilus_trader.adapters.dydx.common.symbol import DYDXSymbol
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol


def test_format_symbol() -> None:
    """
    Test the DYDXSymbol class.
    """
    # Arrange
    symbol = "eth-usdt-perp"

    # Act
    result = DYDXSymbol(symbol)

    # Assert
    assert result == "ETH-USDT"
    assert result.raw_symbol == "ETH-USDT"
    assert result.parse_as_nautilus() == InstrumentId(Symbol("ETH-USDT-PERP"), DYDX_VENUE)
