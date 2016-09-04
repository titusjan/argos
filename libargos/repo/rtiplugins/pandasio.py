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

""" Repository Tree Items (RTI) that store Pandas objects.

    See: http://pandas.pydata.org/
"""
import logging, os
import pandas as pd

from libargos.repo.baserti import BaseRti
from libargos.repo.iconfactory import RtiIconFactory
from libargos.utils.cls import check_class

logger = logging.getLogger(__name__)


class PandasSeriesRti(BaseRti):
    """ Represents a Pandas NDFrame (or None for undefined/unopened nodes)

    """
    _defaultIconGlyph = RtiIconFactory.ARRAY
    _defaultIconColor = RtiIconFactory.COLOR_MEMORY

    def __init__(self, series, nodeName='', fileName='',
                 iconColor=_defaultIconColor):
        """ Constructor.
            :param series: the underlying pandas object. May be undefined (None)
            :type series: NDFrame
        """
        super(PandasSeriesRti, self).__init__(nodeName=nodeName, fileName=fileName)
        check_class(series, (pd.Series, pd.DataFrame))
        self._series = series
        self._iconColor = iconColor

    #
    # @property
    # def isCompound(self):
    #     """ Returns True if the variable has a compound type, otherwise returns False.
    #     """
    #     return self._array is not None and bool(self._array.dtype.names)


    def hasChildren(self):
        """ Returns True if the variable has a compound type, otherwise returns False.
        """
        return self._series is not None


    @property
    def isSliceable(self):
        """ Returns True if the underlying series is not None.
        """
        return self._series is not None


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Passes the index through to the underlying array.
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._series.values.__getitem__(index)
        #return self._series.to_records(index=False).__getitem__(index)


    @property
    def nDims(self):
        """ The number of dimensions of the series, which is always 1
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._series.ndim


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._series.shape


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        if self._series is None:
            return super(PandasSeriesRti, self).elementTypeName
        else:
            try:
                return str(self._series.dtype) # Series
            except AttributeError:
                return '<compound>' # DataFrames and Panels


    def _subNames(self):
        """ The labels of the sub division of the NDFrame.

            Returns [] for Series, columns for DataFrames, items for Panels and labels for Panel4D
        """
        if self.nDims == 1:
            return []
        elif self.nDims == 2:
            return self._series.columns
        elif self.nDims == 3:
            return self._series.items
        elif self.nDims == 4:
            return self._series.labels
        else:
            raise ValueError("_subNames not defined for dimension: ".format(self.ndim))


    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains.
            Only variables with a compound data type can have fields.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"
        assert self._series is not None, "No underlying pandas object"

        childItems = []
        for subName in self._subNames():
            childItem = PandasSeriesRti(self._series[subName], nodeName=subName,
                                        fileName=self.fileName, iconColor=self._iconColor)
            childItems.append(childItem)

        return childItems

