# -*- coding: utf-8 -*-

# This file is part of Argos.
#
# Argos is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Argos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Argos. If not, see <http://www.gnu.org/licenses/>.

"""
Class for storing values and a mask. Masked arrays would have been a good sollution but
unfortunately they are very buggy.
"""

import logging

import numpy as np
import numpy.ma as ma

from libargos.utils.cls import is_an_array, check_is_an_array, check_class

logger = logging.getLogger(__name__)


class ArrayWithMask(object):
    """ Class for storing an arrays together with a mask.

        Used instead of the Numpy MaskedArray class, which has too many issues.
    """
    def __init__(self, data, mask, fill_value):
        """ Constructor

            :param data:
            :param mask:
            :param fill_value:
        """
        check_is_an_array(data)
        check_class(mask, (np.ndarray, bool))
        self.data = data
        self.mask = mask
        self.fill_value= fill_value


    @classmethod
    def createFromMaskedArray(cls, masked_arr):
        """ Creates an ArrayWithMak

        :param masked_arr: a numpy MaskedArray
        :return:
        """
        return cls(masked_arr.data, masked_arr.mask, masked_arr.fill_value)



def transpose(awm, *args, **kwargs):
    """ Tranposes the array and mask separately

        :param awm: ArrayWithMask
        :return:
    """
    awm.data = np.transpose(awm.data)

    if is_an_array(awm.mask):
        awm.mask = np.transpose(awm.mask)

    return awm
