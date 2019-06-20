#!/usr/bin/env python3
# -------------------------------------------------------------------------------------------------
# <copyright file="commands.pxd" company="Invariance Pte">
#  Copyright (C) 2018-2019 Invariance Pte. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  http://www.invariance.com
# </copyright>
# -------------------------------------------------------------------------------------------------

# cython: language_level=3, boundscheck=False, wraparound=False, nonecheck=False

from cpython.datetime cimport datetime

from inv_trader.core.message cimport Message
from inv_trader.model.identifiers cimport GUID, OrderId, TraderId, StrategyId, PositionId
from inv_trader.model.objects cimport ValidString, Price
from inv_trader.model.order cimport Order, AtomicOrder


cdef class Command(Message):
    """
    The base class for all commands.
    """
    pass


cdef class CollateralInquiry(Command):
    """
    Represents a request for a FIX collateral inquiry of all connected accounts.
    """


cdef class SubmitOrder(Command):
    """
    Represents a command to submit an order.
    """
    cdef readonly TraderId trader_id
    cdef readonly StrategyId strategy_id
    cdef readonly PositionId position_id
    cdef readonly Order order


cdef class SubmitAtomicOrder(Command):
    """
    Represents a command to submit an atomic order.
    """
    cdef readonly TraderId trader_id
    cdef readonly StrategyId strategy_id
    cdef readonly PositionId position_id
    cdef readonly AtomicOrder atomic_order


cdef class ModifyOrder(Command):
    """
    Represents a command to modify an order with the modified price.
    """
    cdef readonly TraderId trader_id
    cdef readonly StrategyId strategy_id
    cdef readonly OrderId order_id
    cdef readonly Price modified_price


cdef class CancelOrder(Command):
    """
    Represents a command to cancel an order.
    """
    cdef readonly TraderId trader_id
    cdef readonly StrategyId strategy_id
    cdef readonly OrderId order_id
    cdef readonly ValidString cancel_reason
