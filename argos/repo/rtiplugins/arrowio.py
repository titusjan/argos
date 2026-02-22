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

""" Repository Tree Items (RTIs) for Parquet, IPC and other files that can be read with pyarrow.

    It uses the pyarrow.dataset package to open multiple file formats.
    See https://arrow.apache.org/docs/cpp/dataset.html
    and https://arrow.apache.org/docs/python/api/dataset.html
"""
from __future__ import absolute_import

import logging, os
from typing import Optional

import pyarrow as pa
import pyarrow.dataset as ds

from argos.repo.iconfactory import RtiIconFactory
from argos.repo.baserti import BaseRti
from argos.repo.registry import ICON_COLOR_ARROW, ICON_COLOR_UNDEF
from argos.utils.cls import checkType

logger = logging.getLogger(__name__)



class ArrowColumnRti(BaseRti):
    """ Contains column of a pyarrow Dataset.
    """

    _defaultIconGlyph = RtiIconFactory.ARRAY

    def __init__(self,
                 chunkedArray: pa.ChunkedArray,
                 nodeName: str,
                 fileName: str ='',
                 iconColor: str = ICON_COLOR_UNDEF):
        """ Constructor
        """
        super().__init__(nodeName, fileName=fileName, iconColor=iconColor)
        checkType(chunkedArray, pa.ChunkedArray)
        self._chunkedArray = chunkedArray
        self._npArray = self._chunkedArray.to_numpy()


    @property
    def _isStructured(self):
        """ Returns True, because the table contains a list of
        """
        return False  # TODO:


    @property
    def isSliceable(self):
        """ Returns True if the underlying array is not None.
        """
        return self._npArray is not None


    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
        """
        return self._npArray[index]


    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._npArray.ndim


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
        """
        return self._npArray.shape


    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return "array"


    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return self._npArray.dtype.name  # TODO: look at pillow

    #
    # @property
    # def typeName(self):
    #     """ String representation of the type. By default, the elementTypeName + dimensionality.
    #     """
    #     return dataSetType(self._h5Dataset.dtype, self.dimensionality)

    #
    # @property
    # def attributes(self):
    #     """ The attributes dictionary.
    #     """
    #     return attrsToDict(self._h5Dataset.attrs)



class ArrowDatasetRti(BaseRti):
    """ Reads a file using the pyarrow dataset API.
        See https://arrow.apache.org/docs/cpp/dataset.html
    """
    _defaultIconGlyph = RtiIconFactory.FILE
    _fileFormat = None

    def __init__(self, nodeName, fileName='', iconColor=ICON_COLOR_ARROW):
        """ Constructor
        """
        super().__init__(nodeName, iconColor=iconColor, fileName=fileName)
        self._checkFileExists()
        self._dataset: Optional[ds.Dataset] = None
        self._table: Optional[pa.Table] = None


    def _openResources(self):
        """ Opens the root Dataset.
        """
        logger.info("Opening: {}".format(self._fileName))
        if not os.path.isfile(self._fileName):
            raise OSError("{} does not exist or is not a regular file.".format(self._fileName))

        self._dataset = ds.dataset(self._fileName, format=self._fileFormat)
        self._table = self._dataset.to_table()


    def _closeResources(self):
        """ Closes the root Dataset.
        """
        logger.info("Closing: {}".format(self._fileName))
        self._table = None
        self._dataset = None



    def _fetchAllChildren(self):
        """ Fetches children items.

            If this is stand-alone DataFrame the index, column etc are added as PandasIndexRti obj.
        """
        #assert self.isSliceable, "No underlying pandas object: self._ndFrame is None"

        childItems = []

        for colName, column in zip(self._table.column_names, self._table.itercolumns()):
            logger.debug("Fetching column: {} (type={})".format(colName, type(column)))

            childItem = ArrowColumnRti(
                chunkedArray=column,
                nodeName=colName,
                fileName=self._fileName,
                iconColor=self.iconColor)
            childItems.append(childItem)

        return childItems



class ArrowIpcDatasetRti(ArrowDatasetRti):
    """ Reads an IPC/feather/arrow file using the pyarrow dataset API.
        See https://arrow.apache.org/docs/cpp/dataset.html
    """
    _fileFormat = "ipc"



class ArrowParquetDatasetRti(ArrowDatasetRti):
    """ Reads a parquet file using the pyarrow dataset API.
        See https://arrow.apache.org/docs/cpp/dataset.html
    """
    _fileFormat = "parquet"

