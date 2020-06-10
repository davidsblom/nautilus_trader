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

from nautilus_trader.indicators.base.indicator cimport Indicator


cdef class HilbertSignalNoiseRatio(Indicator):
    cdef double _i_mult
    cdef double _q_mult
    cdef double _range_floor
    cdef double _amplitude_floor
    cdef object _inputs
    cdef object _detrended_prices
    cdef object _in_phase
    cdef object _quadrature
    cdef double _previous_range
    cdef double _previous_amplitude
    cdef double _previous_value
    cdef double _range
    cdef double _amplitude

    cdef readonly int period
    cdef readonly double value

    cpdef void update(self, double high, double low)
    cdef void _calc_hilbert_transform(self)
    cdef double _calc_amplitude(self)
    cdef double _calc_signal_noise_ratio(self)
    cpdef void reset(self)
