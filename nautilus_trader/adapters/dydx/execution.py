"""
Provide an execution client for the `DYDX` decentralized crypto exchange.
"""

import asyncio

import msgspec
import pandas as pd

from nautilus_trader.adapters.dydx.common.constants import DYDX_VENUE
from nautilus_trader.adapters.dydx.common.credentials import get_wallet_address
from nautilus_trader.adapters.dydx.common.enums import DYDXEnumParser
from nautilus_trader.adapters.dydx.config import DYDXExecClientConfig
from nautilus_trader.adapters.dydx.http.account import DYDXAccountHttpAPI
from nautilus_trader.adapters.dydx.http.client import DYDXHttpClient
from nautilus_trader.adapters.dydx.http.errors import DYDXError
from nautilus_trader.adapters.dydx.providers import DYDXInstrumentProvider
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsMessageGeneral
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsSubaccountsChannelData
from nautilus_trader.adapters.dydx.schemas.ws import DYDXWsSubaccountsSubscribed
from nautilus_trader.adapters.dydx.websocket.client import DYDXWebsocketClient
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.reports import FillReport
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import VenueOrderId


class DYDXExecutionClient(LiveExecutionClient):
    """
    Provide an execution client for the `DYDX` decentralized crypto exchange.

    Parameters
    ----------
    loop : asyncio.AbstractEventLoop
        The event loop for the client.
    client : DYDXHttpClient
        The DYDX HTTP client.
    msgbus : MessageBus
        The message bus for the client.
    cache : Cache
        The cache for the client.
    clock : LiveClock
        The clock for the client.
    instrument_provider : DYDXInstrumentProvider
        The instrument provider.
    base_url_ws : str
        The base URL for the WebSocket client.
    config : DYDXExecClientConfig
        The configuration for the client.
    name : str, optional
        The custom client ID.

    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client: DYDXHttpClient,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        instrument_provider: DYDXInstrumentProvider,
        base_url_ws: str,
        config: DYDXExecClientConfig,
        name: str | None,
    ) -> None:
        """
        Provide an execution client for the `DYDX` decentralized crypto exchange.
        """
        account_type = AccountType.MARGIN

        super().__init__(
            loop=loop,
            client_id=ClientId(name or DYDX_VENUE.value),
            venue=DYDX_VENUE,
            oms_type=OmsType.NETTING,
            instrument_provider=instrument_provider,
            account_type=account_type,
            base_currency=None,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
        )

        self._wallet_address = config.wallet_address or get_wallet_address(
            is_testnet=config.testnet,
        )
        self._subaccount = config.subaccount
        self._enum_parser = DYDXEnumParser()
        account_id = AccountId(f"{name or DYDX_VENUE.value}-001")
        self._set_account_id(account_id)

        # WebSocket API
        self._ws_client = DYDXWebsocketClient(
            clock=clock,
            handler=self._handle_ws_message,
            base_url=base_url_ws,
            loop=loop,
        )

        # Http API
        self._http_account = DYDXAccountHttpAPI(
            client=client,
            clock=clock,
        )

        # Decoders
        self._decoder_ws_msg_general = msgspec.json.Decoder(DYDXWsMessageGeneral)
        self._decoder_ws_msg_subaccounts_subscribed = msgspec.json.Decoder(
            DYDXWsSubaccountsSubscribed,
        )
        self._decoder_ws_msg_subaccounts_channel = msgspec.json.Decoder(
            DYDXWsSubaccountsChannelData,
        )

    async def _connect(self) -> None:
        await self._ws_client.connect()

        await self._ws_client.subscribe_account_update(
            wallet_address=self._wallet_address,
            subaccount_number=self._subaccount,
        )

    async def _disconnect(self) -> None:
        await self._ws_client.unsubscribe_account_update(
            wallet_address=self._wallet_address,
            subaccount_number=self._subaccount,
        )
        await self._ws_client.disconnect()

    async def generate_order_status_reports(
        self,
        instrument_id: InstrumentId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
        open_only: bool = False,
    ) -> list[OrderStatusReport]:
        """
        Create an order status report.
        """
        self._log.info("Requesting OrderStatusReports...")
        reports: list[OrderStatusReport] = []

        try:
            dydx_orders = await self._http_account.get_orders(
                address=self._wallet_address,
                subaccount_number=self._subaccount,
            )

            for dydx_order in dydx_orders:
                report = dydx_order.parse_to_order_status_report(
                    account_id=self.account_id,
                    report_id=UUID4(),
                    enum_parser=self._enum_parser,
                    ts_init=self._clock.timestamp_ns(),
                )
                reports.append(report)
        except DYDXError as e:
            self._log.error(f"Failed to generate OrderStatusReports: {e}")

        len_reports = len(reports)
        plural = "" if len_reports == 1 else "s"
        self._log.info(f"Received {len(reports)} OrderStatusReport{plural}")

        return reports

    async def generate_fill_reports(
        self,
        instrument_id: InstrumentId | None = None,
        venue_order_id: VenueOrderId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> list[FillReport]:
        """
        Create an order fill report.
        """
        self._log.info("Requesting FillReports...")
        reports: list[FillReport] = []

        try:
            dydx_fills = await self._http_account.get_fills(
                address=self._wallet_address,
                subaccount_number=self._subaccount,
            )

            for dydx_fill in dydx_fills.fills:
                report = dydx_fill.parse_to_fill_report(
                    account_id=self.account_id,
                    report_id=UUID4(),
                    enum_parser=self._enum_parser,
                    ts_init=self._clock.timestamp_ns(),
                )
                reports.append(report)

        except DYDXError as e:
            self._log.error(f"Failed to generate FillReports: {e}")

        len_reports = len(reports)
        plural = "" if len_reports == 1 else "s"
        self._log.info(f"Received {len(reports)} FillReport{plural}")
        return reports

    async def generate_position_status_reports(
        self,
        instrument_id: InstrumentId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> list[PositionStatusReport]:
        """
        Generate position status reports.
        """
        self._log.info("Requesting PositionStatusReports...")
        reports: list[PositionStatusReport] = []

        try:
            dydx_positions = await self._http_account.get_perpetual_positions(
                address=self._wallet_address,
                subaccount_number=self._subaccount,
            )

            for dydx_position in dydx_positions.positions:
                report = dydx_position.parse_to_position_status_report(
                    account_id=self.account_id,
                    report_id=UUID4(),
                    enum_parser=self._enum_parser,
                    ts_init=self._clock.timestamp_ns(),
                )
                reports.append(report)

        except DYDXError as e:
            self._log.error(f"Failed to generate PositionStatusReports: {e}")

        len_reports = len(reports)
        plural = "" if len_reports == 1 else "s"
        self._log.info(f"Received {len(reports)} PositionStatusReport{plural}")
        return reports

    def _handle_ws_message(self, raw: bytes) -> None:
        try:
            ws_message = self._decoder_ws_msg_general.decode(raw)

            if ws_message.channel == "v4_subaccounts" and ws_message.type == "channel_data":
                self._handle_subaccounts_channel_data(raw)
            elif ws_message.channel == "v4_subaccounts" and ws_message.type == "subscribed":
                self._handle_subaccounts_subscribed(raw)
            elif ws_message.type == "unsubscribed":
                self._log.info(
                    f"Unsubscribed from channel {ws_message.channel} for {ws_message.id}",
                )
            elif ws_message.type == "connected":
                self._log.info("Websocket connected")
            else:
                self._log.error(f"Unknown message `{ws_message.type}`: {raw.decode()}")
        except Exception as e:
            self._log.error(f"Failed to parse websocket message: {raw.decode()} with error {e}")

    def _handle_subaccounts_subscribed(self, raw: bytes) -> None:
        try:
            msg: DYDXWsSubaccountsSubscribed = self._decoder_ws_msg_subaccounts_subscribed.decode(
                raw,
            )

            if msg.contents.subaccount is None:
                self._log.error(f"Subaccount {self._wallet_address}/{self._subaccount} not found")

            self._log.debug(f"{msg}")

        except Exception as e:
            self._log.error(
                f"Failed to parse subaccounts subscribed message: {raw.decode()} with error {e}",
            )

    def _handle_subaccounts_channel_data(self, raw: bytes) -> None:
        try:
            msg: DYDXWsSubaccountsChannelData = self._decoder_ws_msg_subaccounts_channel.decode(raw)
            self._log.debug(f"{msg}")

        except Exception as e:
            self._log.error(
                f"Failed to parse subaccounts channel data: {raw.decode()} with error {e}",
            )
