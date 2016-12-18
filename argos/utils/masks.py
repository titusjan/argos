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
Class for storing values and a mask. Masked arrays would have been a good solution but
unfortunately they are very buggy.
"""

import logging

import numpy as np
import numpy.ma as ma

from argos.utils.cls import check_class, is_an_array, check_is_an_array, array_is_structured

logger = logging.getLogger(__name__)


class ConsistencyError(Exception):
    """ Raised when the mask of an ArrayWithMask object has an inconsitstent shape."""
    pass


class ArrayWithMask(object):
    """ Class for storing an arrays together with a mask.

        Used instead of the Numpy MaskedArray class, which has too many issues.
    """
    def __init__(self, data, mask, fill_value):
        """ Constructor

            :param data:
            :param mask: array with mask or single boolean for the complete mask
            :param fill_value:
        """
        check_is_an_array(data)
        check_class(mask, (np.ndarray, bool, np.bool_))

        # Init fields
        self._data = None
        self._mask = None
        self._fill_value= None

        # Use setters
        self.data = data
        self.mask = mask
        self.fill_value= fill_value


    @property
    def data(self):
        """ The array values. Will be a numpy array."""
        return self._data


    @data.setter
    def data(self, values):
        """ The array values. Must be a numpy array."""
        check_is_an_array(values)
        self._data = values


    @property
    def mask(self):
        """ The mask values. Will be an array or a boolean scalar."""
        return self._mask


    @mask.setter
    def mask(self, mask):
        """ The mask values. Must be an array or a boolean scalar."""
        check_class(mask, (np.ndarray, bool, np.bool_))
        if isinstance(mask, (bool, np.bool_)):
            self._mask = bool(mask)
        else:
            self._mask = mask


    @property
    def fill_value(self):
        """ The fill_value."""
        return self._fill_value


    @fill_value.setter
    def fill_value(self, fill_value):
        """ The fill_value."""
        self._fill_value = fill_value


    def checkIsConsistent(self):
        """ Raises a ConsistencyError if the mask has an incorrect shape.
        """
        if is_an_array(self.mask) and self.mask.shape != self.data.shape:
            raise ConsistencyError("Shape mismatch mask={}, data={}"
                                   .format(self.mask.shape != self.data.shape))


    @classmethod
    def createFromMaskedArray(cls, masked_arr):
        """ Creates an ArrayWithMak

            :param masked_arr: a numpy MaskedArray or numpy array
            :return: ArrayWithMask
        """
        if isinstance(masked_arr, ArrayWithMask):
            return masked_arr

        check_class(masked_arr, (np.ndarray, ma.MaskedArray))

        # A MaskedConstant (i.e. masked) is a special case of MaskedArray. It does not seem to have
        # a fill_value so we use None to use the default.
        # https://docs.scipy.org/doc/numpy/reference/maskedarray.baseclass.html#numpy.ma.masked
        fill_value = getattr(masked_arr, 'fill_value', None)

        return cls(masked_arr.data, masked_arr.mask, fill_value)


    def asMaskedArray(self):
        """ Creates converts to a masked array
        """
        return ma.masked_array(data=self.data, mask=self.mask, fill_value=self.fill_value)


    def maskAt(self, index):
        """ Returns the mask at the index.

            It the mask is a boolean it is returned since this boolean representes the mask for
            all array elements.
        """
        if isinstance(self.mask, bool):
            return self.mask
        else:
            return self.mask[index]


    def maskIndex(self):
        """ Returns a boolean index with True if the value is masked.

            Always has the same shape as the maksedArray.data, event if the mask is a single boolan.
        """
        if isinstance(self.mask, bool):
            return np.full(self.data.shape, self.mask, dtype=np.bool)
        else:
            return self.mask


    @property
    def shape(self):
        """ Convenience method, returns the shape of the data.
        """
        return self.data.shape


    @property
    def dtype(self):
        """ Convenience method, returns the dtype of the data.
        """
        return self.data.dtype


    def __getitem__(self, index):
        """ Called when using the awm with an index (e.g. rti[0]).

            Convenience method, applies the index of the data.
        """
        return self.data[index]


    def transpose(self, *args, **kwargs):
        """ Transposes the array and mask separately

            :param awm: ArrayWithMask
            :return: copy/view with transposed
        """
        tdata = np.transpose(self.data, *args, **kwargs)
        tmask = np.transpose(self.mask, *args, **kwargs) if is_an_array(self.mask) else self.mask
        return ArrayWithMask(tdata, tmask, self.fill_value)


    def replaceMaskedValue(self, replacementValue):
        """ Replaces values where the mask is True with the replacement value.
        """
        if self.mask is False:
            pass
        elif self.mask is True:
            self.data[:] = replacementValue
        else:
            self.data[self.mask] = replacementValue


    def replaceMaskedValueWithNan(self):
        """ Replaces values where the mask is True with the replacement value.

            Will change the data type to float if the data is an integer.
            If the data is not a float (or int) the function does nothing.
        """
        kind = self.data.dtype.kind
        if kind == 'i' or kind == 'u': # signed/unsigned int
            self.data = self.data.astype(np.float, casting='safe')

        if self.data.dtype.kind != 'f':
            return # only replace for floats

        if self.mask is False:
            pass
        elif self.mask is True:
            self.data[:] = np.NaN
        else:
            self.data[self.mask] = np.NaN


#############
# functions #
#############

def replaceMaskedValue(data, mask, replacementValue, copyOnReplace=True):
    """ Replaces values where the mask is True with the replacement value.

        :copyOnReplace makeCopy: If True (the default) it makes a copy if data is replaced.
    """
    if mask is False:
        result = data
    elif mask is True:
        result = np.copy(data) if copyOnReplace else data
        result[:] = replacementValue
    else:
        #logger.debug("############ count_nonzero: {}".format(np.count_nonzero(mask)))
        if copyOnReplace and np.any(mask):
            #logger.debug("Making copy")
            result = np.copy(data)
        else:
            result = data

        result[mask] = replacementValue

    return result


def replaceMaskedValueWithFloat(data, mask, replacementValue, copyOnReplace=True):
    """ Replaces values where the mask is True with the replacement value.

        Will change the data type to float if the data is an integer.
        If the data is not a float (or int) the function does nothing. Otherwise it will call
        replaceMaskedValue with the same parameters.

        :copyOnReplace makeCopy: If True (the default) it makes a copy if data is replaced.
    """
    kind = data.dtype.kind
    if kind == 'i' or kind == 'u': # signed/unsigned int
        data = data.astype(np.float, casting='safe')

    if data.dtype.kind != 'f':
        return # only replace for floats
    else:
        return replaceMaskedValue(data, mask, replacementValue, copyOnReplace=copyOnReplace)



def maskedNanPercentile(maskedArray, percentiles, *args, **kwargs):
    """ Calculates np.nanpercentile on the non-masked values
    """

    #https://docs.scipy.org/doc/numpy/reference/maskedarray.generic.html#accessing-the-data
    awm = ArrayWithMask.createFromMaskedArray(maskedArray)

    maskIdx = awm.maskIndex()
    validData = awm.data[~maskIdx]

    if len(validData) >= 1:
        result = np.nanpercentile(validData, percentiles, *args, **kwargs)
    else:
        # If np.nanpercentile on an empty list only returns a single Nan. We correct this here.
        result = len(percentiles) * [np.nan]

    assert len(result) == len(percentiles), \
        "shape mismatch: {} != {}".format(len(result), len(percentiles))

    return result # as expected



#
# def replace_missing_values(array, missing_value, replacement_value):
#     """ Returns a copy of the array where the missing_values are replaced with replacement_value.
#
#         If missing_value is None, nothing is replaced, a copy of the array is returned..
#         The missing_value can be Nan or infinite, these are replaced.
#
#         If array is a masked array the masked value are replaced (masked_to_regular_array).
#     """
#     if isinstance(array, ma.MaskedArray):
#         logger.debug("^^^^^^^^^^^^^^^^^^^ mask: {}".format(array.mask))
#
#         return array
#         return masked_to_regular_array(array, replacement_value=replacement_value)
#     if missing_value is None:
#         array = np.copy(array)
#     elif np.isnan(missing_value):
#         array[np.isnan(array)] = replacement_value
#     else:
#         array[array == missing_value] = replacement_value
#
#     return array


def fillValuesToNan(masked_array):
    """ Replaces the fill_values of the masked array by NaNs

        If the array is None or it does not contain floating point values, it cannot contain NaNs.
        In that case the original array is returned.
    """
    if masked_array is not None and masked_array.dtype.kind == 'f':
        check_class(masked_array, ma.masked_array)
        logger.debug("Replacing fill_values by NaNs")
        masked_array[:] = ma.filled(masked_array, np.nan)
        masked_array.set_fill_value(np.nan)
    else:
        return masked_array


#TODO: does recordMask help here?
# https://docs.scipy.org/doc/numpy/reference/maskedarray.baseclass.html#numpy.ma.MaskedArray.recordmask
def maskedEqual(array, missingValue):
    """ Mask an array where equal to a given (missing)value.

        Unfortunately ma.masked_equal does not work with structured arrays. See:
        https://mail.scipy.org/pipermail/numpy-discussion/2011-July/057669.html

        If the data is a structured array the mask is applied for every field (i.e. forming a
        logical-and). Otherwise ma.masked_equal is called.
    """
    if array_is_structured(array):
        # Enforce the array to be masked
        if not isinstance(array, ma.MaskedArray):
            array = ma.MaskedArray(array)

        # Set the mask separately per field
        for nr, field in enumerate(array.dtype.names):
            if hasattr(missingValue, '__len__'):
                fieldMissingValue = missingValue[nr]
            else:
                fieldMissingValue = missingValue

            array[field] = ma.masked_equal(array[field], fieldMissingValue)

        check_class(array, ma.MaskedArray) # post-condition check
        return array
    else:
        # masked_equal works with missing is None
        result = ma.masked_equal(array, missingValue, copy=False)
        check_class(result, ma.MaskedArray) # post-condition check
        return result
