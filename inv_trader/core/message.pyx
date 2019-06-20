#!/usr/bin/env python3
# -------------------------------------------------------------------------------------------------
# <copyright file="message.pyx" company="Invariance Pte">
#  Copyright (C) 2018-2019 Invariance Pte. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  http://www.invariance.com
# </copyright>
# -------------------------------------------------------------------------------------------------

# cython: language_level=3, boundscheck=False, wraparound=False, nonecheck=False

from cpython.datetime cimport datetime

from inv_trader.model.identifiers cimport GUID


cdef class Message:
    """
    The base class for all messages.
    """

    def __init__(self, GUID identifier, datetime timestamp):
        """
        Initializes a new instance of the Response abstract class.

        :param identifier: The message identifier.
        :param timestamp: The message timestamp.
        """
        self.id = identifier
        self.timestamp = timestamp

    cdef bint equals(self, Message other):
        """
        Return a value indicating whether the given message is equal to this message.
        
        :param other: The other message to compare
        :return: True if the messages are equal, otherwise False.
        """
        if isinstance(other, self.__class__):
            return self.id == other.id
        else:
            return False

    def __eq__(self, Message other) -> bool:
        """
        Return a value indicating whether the given message is equal to this message.

        :param other: The other message to compare
        :return: True if the messages are equal, otherwise False.
        """
        return self.equals(other)

    def __ne__(self, Message other):
        """
        Return a value indicating whether the given message is not equal to this message.

        :param other: The other message to compare
        :return: True if the messages are not equal, otherwise False.
        """
        return not self.equals(other)

    def __hash__(self) -> int:
        """"
        Return the hash for this message.

        :return: int.
        """
        return hash(self.id)

    def __str__(self) -> str:
        """
        Return the str() string representation of this message.

        :return: str.
        """
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self) -> str:
        """
        Return the repr() string representation of this message.

        :return: str.
        """
        return f"<{str(self)} object at {id(self)}>"
