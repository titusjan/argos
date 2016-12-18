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

""" Stores for representing data that is read from text files.
"""
import logging, os
import numpy as np

from numpy.lib.npyio import NpzFile

from argos.qt import QtWidgets
from argos.repo.iconfactory import RtiIconFactory
from argos.repo.memoryrtis import ArrayRti, SliceRti, MappingRti
from argos.utils.cls import check_is_an_array, check_class

logger = logging.getLogger(__name__)

ICON_COLOR_NUMPY = '#987456'

# Do not allow pickle in numpy.load(), at least for now. This can be a security risk
ALLOW_PICKLE = False



class NumpyTextFileRti(ArrayRti):
    """ Reads a 2D array from a simple text file using numpy.loadtxt().
    """
    _defaultIconGlyph = RtiIconFactory.FILE
    _defaultIconColor = ICON_COLOR_NUMPY

    def __init__(self, nodeName='', fileName=''):
        """ Constructor. Initializes as an ArrayRTI with None as underlying array.
        """
        super(NumpyTextFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName,
                                               iconColor=self._defaultIconColor)
        self._checkFileExists()


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return True


    def _openResources(self):
        """ Uses numpy.loadtxt to open the underlying file
        """
        self._array = np.loadtxt(self._fileName, ndmin=0)


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._array = None


    def _fetchAllChildren(self):
        """ Adds an ArrayRti per column as children so that they can be inspected easily
        """
        childItems = []
        _nRows, nCols = self._array.shape if self._array is not None else (0, 0)
        for col in range(nCols):
            colItem = SliceRti(self._array[:, col], nodeName="column-{}".format(col),
                               fileName=self.fileName, iconColor=self.iconColor,
                               attributes=self.attributes)
            childItems.append(colItem)
        return childItems




class NumpyBinaryFileRti(ArrayRti):
    """ Reads a Numpy array from a binary file (.npy) using numpy.load().

        The file must have been saved with numpy.save() and therefore contain a single arrays.
        A TypeError is raised if this is not the case.

        The allow_pickle is set to False, no object arrays can be read.
    """
    _defaultIconGlyph = RtiIconFactory.FILE
    _defaultIconColor = ICON_COLOR_NUMPY

    def __init__(self, nodeName='', fileName=''):
        """ Constructor. Initializes as an ArrayRTI with None as underlying array.
        """
        super(NumpyBinaryFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName,
                                                 iconColor=self._defaultIconColor)
        self._checkFileExists()


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children

            Returns True so that the file can be opened, even though the array has no children.
        """
        return True


    def _openResources(self):
        """ Uses numpy.load to open the underlying file
        """
        arr = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_is_an_array(arr)
        self._array = arr


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._array = None



class NumpyCompressedFileRti(MappingRti):
    """ Reads arrays from a Numpy zip file (.npz) using numpy.load().

        The file must have been saved with numpy.savez() and therefore contain multiple arrays.
        A TypeError is raised if this is not the case.

        The allow_pickle is set to False, no object arrays can be read.
    """
    _defaultIconGlyph = RtiIconFactory.FILE
    _defaultIconColor = ICON_COLOR_NUMPY

    def __init__(self, nodeName='', fileName=''):
        """ Constructor. Initializes as an MappingRti with None as underlying dictionary.
        """
        super(NumpyCompressedFileRti, self).__init__(None,
                                                     nodeName=nodeName, fileName=fileName,
                                                     iconColor=self._defaultIconColor)
        self._checkFileExists()


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return True


    def _openResources(self):
        """ Uses numpy.load to open the underlying file
        """
        dct = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_class(dct, NpzFile)
        self._dictionary = dct


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._dictionary = None

