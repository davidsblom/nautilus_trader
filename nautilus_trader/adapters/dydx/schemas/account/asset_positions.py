"""
Define the schemas for the GetAssetPositions endpoint.
"""

# ruff: noqa: N815

import msgspec

from nautilus_trader.adapters.dydx.schemas.account.address import DYDXAssetPosition


class DYDXAssetPositionsResponse(msgspec.Struct, forbid_unknown_fields=True):
    """
    Define the schema for the asset positions response.
    """

    positions: list[DYDXAssetPosition]
