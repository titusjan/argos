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
from __future__ import absolute_import

import logging
import numpy as np
import pandas as pd

from pandas.core.generic import NDFrame

from argos.repo.baserti import BaseRti, shapeToSummary
from argos.repo.iconfactory import RtiIconFactory, ICON_COLOR_UNDEF
from argos.utils.cls import check_class

logger = logging.getLogger(__name__)


class PandasIndexRti(BaseRti):
    """ Contains a Pandas undex.
    """
    _defaultIconGlyph = RtiIconFactory.DIMENSION

    def __init__(self, index=None, nodeName='', fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor

            The Index is not part of Pandas' documented API, although it is not private either,
            many methods return a pd.core.index.Index, but the class itself is not documented.
            We therefore don't check if index is of the correct type, as it is not clear if
            pd.core.index.Index is the ancestor of all panda index objects.

            :param index: the underlying pandas index.
        """
        super(PandasIndexRti, self).__init__(nodeName=nodeName, fileName=fileName,
                                             iconColor=iconColor)

        self._index = index


    def hasChildren(self):
        """ Returns False. An index never has child nodes.
        """
        return False


    @property
    def isSliceable(self):
        """ Returns True because the underlying index is sliceable.
        """
        return True


    def __getitem__(self, idx):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Returns np.array(index[idx]), where index is the underlying Pandas index.
        """
        return np.array(self._index.__getitem__(idx))


    @property
    def nDims(self):
        """ The number of dimensions of the index. Will always be 1.
        """
        result = self._index.ndim
        assert result == 1, "Expected index to be 1D, got: {}D".format(result)
        return result


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying index.
        """
        return self._index.shape


    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return "index"


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        try:
            return str(self._index.dtype) # Series
        except AttributeError:
            assert False, "not yet implemented." # TODO multi-indexes
            return '<structured>' # DataFrames and Panels


    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.
        """
        return shapeToSummary(self.arrayShape)



class AbstractPandasNDFrameRti(BaseRti):
    """ Contains a Pandas NDFrame object.

        The NDFrame class is the ancestor of pandas Series, DataFrame and Panels.
        May contain None as well (for unopened nodes).

        This is an abstract class and should not be created directly. Use one of its subclasses
        instead.
    """
    # Show always an array, even when _standAlone is false. In this case the NDFrame is a slice of
    # a higher-dimensional NDFrame, so the Field glyph, does not apply (fields have the same nr
    # of dimensions as their parents).
    _defaultIconGlyph = RtiIconFactory.ARRAY

    def __init__(self, ndFrame=None, nodeName='', fileName='', standAlone=True,
                 iconColor=ICON_COLOR_UNDEF):
        """ Constructor

            The NDFrame is not part of Pandas' documented API, although it mentions this
            inheritance. Therefore it is not checked the ndFrame is actually of type NDFrame.

            :param ndFrame: the underlying pandas object. May be undefined (None)
            :type ndFrame: pandas.core.generic.NDFrame
            :param standAlone: True if the NDFrame is a stand-alone object, False if it is part of
                another higher-dimensional, NDFrame. This influences the array. Furthermore, if
                standAlone is True the index of the NDFrame will be included when the children
                are fetched and included in the tree (as a PandasIndexRti)
        """
        super(AbstractPandasNDFrameRti, self).__init__(
            nodeName=str(nodeName), fileName=fileName, iconColor = iconColor)

        check_class(ndFrame, NDFrame, allow_none=True)
        self._ndFrame = ndFrame
        self._standAlone = standAlone


    @property
    def _isStructured(self):
        """ Returns True if the class can be subdivided in separate fields.

            Abstract method, will be overridden in the descendants.

            A DataFrame is structured because it is composed of multiple Series. A Series can not
            be subdivided further and thus will return False.
        """
        raise NotImplementedError()


    def hasChildren(self):
        """ Returns True if the variable has a structured type, otherwise returns False.
        """
        return self._ndFrame is not None and (self._isStructured or self._standAlone)


    @property
    def isSliceable(self):
        """ Returns True if the underlying series is not None.
        """
        return self._ndFrame is not None


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Passes the index through to the values property of the underlying NDFrame.
        """
        assert self.isSliceable, "No underlying pandas object: self._ndFrame is None"
        return self._ndFrame.values.__getitem__(index)


    @property
    def nDims(self):
        """ The number of dimensions of the pandas object.
        """
        assert self.isSliceable, "No underlying pandas object: self._ndFrame is None"
        return self._ndFrame.ndim


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying pandas object.
        """
        assert self.isSliceable, "No underlying pandas object: self._ndFrame is None"
        return self._ndFrame.shape


    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return "array"


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        if self._ndFrame is None:
            return super(AbstractPandasNDFrameRti, self).elementTypeName
        else:
            try:
                return str(self._ndFrame.dtype) # Series
            except AttributeError:
                return 'compound' # DataFrames and Panels


    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.
        """
        if self._ndFrame is None:
            return ""
        else:
            return shapeToSummary(self.arrayShape)


    def _createIndexRti(self, index, nodeName):
        """ Auxiliary method that creates a PandasIndexRti.
        """
        return PandasIndexRti(index=index, nodeName=nodeName, fileName=self.fileName,
                              iconColor=self.iconColor)



class PandasSeriesRti(AbstractPandasNDFrameRti):
    """ Contains a Pandas Series.
    """
    @property
    def _isStructured(self):
        """ Returns False, because Series cannot be further subdivided.
        """
        return False


    @property
    def dimensionNames(self):
        """ Returns a list with names that correspond to every NDFrame dimension.
            For Series this is: ['index']
        """
        return ['index']


    def _fetchAllChildren(self):
        """ Fetches the index if the showIndex member is True

            Descendants can override this function to add the subdevicions.
        """
        assert self.isSliceable, "No underlying pandas object: self._ndFrame is None"
        childItems = []
        if self._standAlone:
            childItems.append(self._createIndexRti(self._ndFrame.index, 'index'))
        return childItems



class PandasDataFrameRti(AbstractPandasNDFrameRti):
    """ Contains a Pandas DataFrame
    """
    @property
    def _isStructured(self):
        """ Returns True, because DataFrames consist of Series
        """
        return True


    @property
    def dimensionNames(self):
        """ Returns a list with names that correspond to every NDFrame dimension.
            For DataFrames this is: ['index', 'columns']
        """
        return ['index', 'columns']


    def _fetchAllChildren(self):
        """ Fetches children items.

            If this is stand-alone DataFrame the index, column etc are added as PandasIndexRti obj.
        """
        assert self.isSliceable, "No underlying pandas object: self._ndFrame is None"

        childItems = []

        for subName in self._ndFrame.columns: # Note that this is not the first dimension!
            childItem = PandasSeriesRti(self._ndFrame[subName], nodeName=subName,
                                        fileName=self.fileName, iconColor=self.iconColor,
                                        standAlone=False)
            childItems.append(childItem)

        if self._standAlone:
            childItems.append(self._createIndexRti(self._ndFrame.index, 'index'))
            childItems.append(self._createIndexRti(self._ndFrame.columns, 'columns'))

        return childItems



class PandasCsvFileRti(PandasDataFrameRti):
    """ Reads a comma-separated file (CSV) into a Pandas DataFrame.
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor. Initializes as an ArrayRTI with None as underlying array.
        """
        super(PandasCsvFileRti, self).__init__(ndFrame=None, nodeName=nodeName, fileName=fileName,
                                               iconColor=iconColor, standAlone=True)
        self._checkFileExists()
        self._ndFrame = None


    def hasChildren(self):
        """ Returns True so that a triangle is added that expands the node and opens the file
        """
        return True


    def _openResources(self):
        """ Uses pandas.read_cs to open the underlying file
        """
        self._ndFrame = pd.read_csv(self._fileName, comment='#')


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._ndFrame = None



class PandasHdfFileRti(BaseRti):
    """ Reads Pandas data stored in a HDF-5 file.
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName, fileName='', iconColor=ICON_COLOR_UNDEF):
        """ Constructor
        """
        super(PandasHdfFileRti, self).__init__(
            nodeName=nodeName, fileName=fileName, iconColor=iconColor)

        self._store = None


    def _openResources(self):
        """ Uses pandas HDFStore to open the underlying file
            https://pandas.pydata.org/pandas-docs/stable/io.html#io-hdf5
        """
        self._store = pd.HDFStore(self._fileName)


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._store = None


    def _fetchAllChildren(self):
        """ Fetches all sub groups and variables that this group contains.
        """
        assert self._store is not None, "dataset undefined (file not opened?)"
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []
        for key in self._store.keys():
            if key.startswith('/'):
                logger.debug("Removing leading slash from key {}".format(key))
                key = key[1:]
            logger.debug("Getting object from HdfStore: {}".format(key))
            obj = self._store.get(key)

            if isinstance(obj, pd.Series):
                childItem = PandasSeriesRti(
                    obj, nodeName=key, fileName=self.fileName, iconColor=self.iconColor)
            elif isinstance(obj, pd.DataFrame):
                childItem = PandasDataFrameRti(
                    obj, nodeName=key, fileName=self.fileName, iconColor=self.iconColor)
            elif isinstance(obj, pd.Panel):
                childItem = PandasPanelRti(
                    obj, nodeName=key, fileName=self.fileName, iconColor=self.iconColor)
            else:
                logger.warning("Unexpected child type: {}".format(type(obj)))
                childItem = BaseRti(nodeName=key, fileName=self.fileName, iconColor=self.iconColor)

            childItems.append(childItem)
        return childItems

