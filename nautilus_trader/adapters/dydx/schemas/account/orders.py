"""
Define the schemas for the GetOrders endpoint.
"""

# ruff: noqa: N815

import datetime

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEnumParser
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderSide
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderStatus
from nautilus_trader.adapters.dydx.common.enums import DYDXOrderType
from nautilus_trader.adapters.dydx.common.enums import DYDXTimeInForce
from nautilus_trader.adapters.dydx.common.symbol import DYDXSymbol
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity


class DYDXOrderResponse(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the schema for the order response.
    """

    id: str
    subaccountId: str
    clientId: str
    clobPairId: str
    side: DYDXOrderSide
    size: str
    totalFilled: str
    price: str
    type: DYDXOrderType
    reduceOnly: bool
    orderFlags: str
    clientMetadata: str
    timeInForce: DYDXTimeInForce
    status: DYDXOrderStatus
    postOnly: bool
    ticker: str
    updatedAt: datetime.datetime
    updatedAtHeight: str
    subaccountNumber: float
    goodTilBlock: str | None = None
    goodTilBlockTime: str | None = None
    createdAtHeight: str | None = None
    triggerPrice: str | None = None

    def parse_to_order_status_report(
        self,
        account_id: AccountId,
        report_id: UUID4,
        enum_parser: DYDXEnumParser,
        ts_init: int,
    ) -> OrderStatusReport:
        """
        Create an order status report from the order message.
        """
        return OrderStatusReport(
            account_id=account_id,
            instrument_id=DYDXSymbol(self.ticker).parse_as_nautilus(),
            client_order_id=ClientOrderId(self.clientId),
            venue_order_id=VenueOrderId(self.id),
            order_side=enum_parser.parse_dydx_order_side(self.side),
            order_type=enum_parser.parse_dydx_order_type(self.type),
            time_in_force=enum_parser.parse_dydx_time_in_force(self.timeInForce),
            order_status=enum_parser.parse_dydx_order_status(self.status),
            price=Price.from_str(self.price),
            quantity=Quantity.from_str(self.size),
            filled_qty=Quantity.from_str(self.totalFilled),
            avg_px=None,
            post_only=self.postOnly,
            reduce_only=self.reduceOnly,
            ts_last=dt_to_unix_nanos(self.updatedAt),
            report_id=report_id,
            ts_accepted=0,
            ts_init=ts_init,
        )
