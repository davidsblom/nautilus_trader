# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2020 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU General Public License Version 3.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

from nautilus_trader.indicators.average.moving_average import MovingAverage, MovingAverageType
from nautilus_trader.indicators.average.ama import AdaptiveMovingAverage
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.indicators.average.sma import SimpleMovingAverage
from nautilus_trader.indicators.average.wma import WeightedMovingAverage
from nautilus_trader.indicators.average.hma import HullMovingAverage
from nautilus_trader.core.correctness cimport Condition


cdef class MovingAverageFactory:
    """
    Provides a factory to construct different moving average indicators.
    """

    @staticmethod
    def create(int period,
               object ma_type: MovingAverageType,
               **kwargs) -> MovingAverage:
        """
        Create a moving average indicator corresponding to the given ma_type.

        :param period: The period of the moving average (> 0).
        :param ma_type: The moving average type.
        :return: The moving average indicator.
        """
        Condition.positive(period, 'period')

        if ma_type == MovingAverageType.SIMPLE:
            return SimpleMovingAverage(period)

        elif ma_type == MovingAverageType.EXPONENTIAL:
            return ExponentialMovingAverage(period)

        elif ma_type == MovingAverageType.WEIGHTED:
            return WeightedMovingAverage(period, **kwargs)

        elif ma_type == MovingAverageType.HULL:
            return HullMovingAverage(period)

        elif ma_type == MovingAverageType.ADAPTIVE:
            return AdaptiveMovingAverage(period, **kwargs)
