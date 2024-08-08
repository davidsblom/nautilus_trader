"""
Define common methods for parsing messages from dYdX.
"""

from nautilus_trader.adapters.dydx.common.enums import DYDXCandlesResolution
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import BarAggregation


def get_interval_from_bar_type(bar_type: BarType) -> DYDXCandlesResolution:
    """
    Convert a nautilus bar type to a dYdX candles resolution enum.
    """
    aggregation: BarAggregation = bar_type.spec.aggregation

    bar_type_to_candle_resolution_map = {
        (BarAggregation.MINUTE, 1): DYDXCandlesResolution.ONE_MINUTE,
        (BarAggregation.MINUTE, 5): DYDXCandlesResolution.FIVE_MINUTES,
        (BarAggregation.MINUTE, 15): DYDXCandlesResolution.FIFTEEN_MINUTES,
        (BarAggregation.MINUTE, 30): DYDXCandlesResolution.THIRTY_MINUTES,
        (BarAggregation.MINUTE, 60): DYDXCandlesResolution.ONE_HOUR,
        (BarAggregation.MINUTE, 240): DYDXCandlesResolution.FOUR_HOURS,
        (BarAggregation.HOUR, 1): DYDXCandlesResolution.ONE_HOUR,
        (BarAggregation.HOUR, 4): DYDXCandlesResolution.FOUR_HOURS,
        (BarAggregation.HOUR, 24): DYDXCandlesResolution.ONE_DAY,
        (BarAggregation.DAY, 1): DYDXCandlesResolution.ONE_DAY,
    }

    return bar_type_to_candle_resolution_map[(aggregation, bar_type.spec.step)]
