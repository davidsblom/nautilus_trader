"""
Define the schemas for the GetFills endpoint.
"""

# ruff: noqa: N815

import datetime
from decimal import Decimal

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEnumParser
from nautilus_trader.adapters.dydx.common.enums import DYDXFillType
from nautilus_trader.adapters.dydx.common.enums import DYDXLiquidity
from nautilus_trader.adapters.dydx.common.enums import DYDXMarketType
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderSide
from nautilus_trader.adapters.dydx.common.symbol import DYDXSymbol
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.reports import FillReport
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity


class DYDXFillResponse(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the schema for a fill.
    """

    id: str
    side: DYDXOrderSide
    liquidity: DYDXLiquidity
    type: DYDXFillType
    market: str
    marketType: DYDXMarketType
    price: str
    size: str
    fee: str
    createdAt: datetime.datetime
    createdAtHeight: str
    subaccountNumber: float
    orderId: str | None = None
    clientMetadata: str | None = None

    def parse_to_fill_report(
        self,
        account_id: AccountId,
        report_id: UUID4,
        enum_parser: DYDXEnumParser,
        ts_init: int,
    ) -> FillReport:
        """
        Parse the fill message into a FillReport.
        """
        return FillReport(
            client_order_id=None,
            venue_order_id=VenueOrderId(str(self.orderId)),
            trade_id=TradeId(self.id),
            account_id=account_id,
            instrument_id=DYDXSymbol(self.market).parse_as_nautilus(),
            order_side=enum_parser.parse_dydx_order_side(self.side),
            last_qty=Quantity.from_str(self.size),
            last_px=Price.from_str(self.price),
            liquidity_side=enum_parser.parse_dydx_liquidity_side(self.liquidity),
            commission=Money(Decimal(self.fee), Currency.from_str("USDT")),
            report_id=report_id,
            ts_event=dt_to_unix_nanos(self.createdAt),
            ts_init=ts_init,
        )


class DYDXFillsResponse(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the schema for the fills response.
    """

    fills: list[DYDXFillResponse]
    pageSize: float | None = None
    totalResults: float | None = None
    offset: float | None = None
