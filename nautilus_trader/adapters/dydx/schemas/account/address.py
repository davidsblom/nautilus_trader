"""
Define the schemas for the GetAddress endpoint.
"""

# ruff: noqa: N815

import datetime

import msgspec

from nautilus_trader.adapters.dydx.common.enums import DYDXEnumParser
from nautilus_trader.adapters.dydx.common.enums import DYDXPerpetualPositionStatus
from nautilus_trader.adapters.dydx.common.enums import DYDXPositionSide
from nautilus_trader.adapters.dydx.common.symbol import DYDXSymbol
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.objects import Quantity


class DYDXPerpetualPosition(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the perpetual position.
    """

    market: str
    status: DYDXPerpetualPositionStatus
    side: DYDXPositionSide
    size: str
    maxSize: str
    entryPrice: str
    realizedPnl: str
    createdAt: datetime.datetime
    createdAtHeight: str
    sumOpen: str
    sumClose: str
    netFunding: str
    unrealizedPnl: str
    subaccountNumber: float
    exitPrice: str | None = None
    closedAt: datetime.datetime | None = None

    def parse_to_position_status_report(
        self,
        account_id: AccountId,
        report_id: UUID4,
        enum_parser: DYDXEnumParser,
        ts_init: int,
    ) -> PositionStatusReport:
        """
        Parse the position message into a PositionStatusReport.
        """
        ts_last = dt_to_unix_nanos(self.createdAt)

        if self.closedAt is not None:
            ts_last = dt_to_unix_nanos(self.closedAt)

        return PositionStatusReport(
            account_id=account_id,
            instrument_id=DYDXSymbol(self.market).parse_as_nautilus(),
            position_side=enum_parser.parse_dydx_position_side(self.side),
            quantity=Quantity.from_str(self.size),
            report_id=report_id,
            ts_init=ts_init,
            ts_last=ts_last,
        )


class DYDXAssetPosition(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the asset position.
    """

    symbol: str
    side: DYDXPositionSide
    size: str
    assetId: str
    subaccountNumber: float


class DYDXSubaccount(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the schema for the subaccount response.
    """

    address: str
    subaccountNumber: float
    equity: str
    freeCollateral: str
    openPerpetualPositions: dict[str, DYDXPerpetualPosition]
    assetPositions: dict[str, DYDXAssetPosition]
    marginEnabled: bool
    updatedAtHeight: str | None = None
    latestProcessedBlockHeight: str | None = None


class DYDXSubaccountResponse(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the address response message.
    """

    subaccount: DYDXSubaccount


class DYDXAddressResponse(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the address response message.
    """

    subaccounts: list[DYDXSubaccount]
    totalTradingRewards: str
