"""
Represent a dYdX specific symbol containing a product type suffix.
"""

from __future__ import annotations

from nautilus_trader.adapters.dydx.common.constants import DYDX_VENUE
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol


class DYDXSymbol(str):
    """
    Represent a dYdX specific symbol containing a product type suffix.
    """

    __slots__ = ()

    def __new__(cls, symbol: str) -> DYDXSymbol:  # noqa: PYI034
        """
        Create a new dYdX symbol.
        """
        PyCondition.valid_string(symbol, "symbol")

        # Format the string on construction to be dYdX compatible
        return super().__new__(
            cls,
            symbol.upper().replace(" ", "").replace("/", "").replace("-PERP", ""),
        )

    @property
    def raw_symbol(self) -> str:
        """
        Return the raw Bybit symbol (without the product type suffix).

        Returns
        -------
        str

        """
        return str(self)

    def parse_as_nautilus(self) -> InstrumentId:
        """
        Parse the dYdX symbol into a Nautilus instrument ID.

        Returns
        -------
        InstrumentId

        """
        return InstrumentId(Symbol(str(self) + "-PERP"), DYDX_VENUE)
