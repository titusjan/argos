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

from libargos.qt import QtGui
from libargos.repo.iconfactory import RtiIconFactory
from libargos.repo.memoryrtis import ArrayRti

logger = logging.getLogger(__name__)

ICON_COLOR_NUMPY = '#8800FF'



class NumpyTextColumnRti(ArrayRti):
    """ A column in a numpy text file. Will typically be a child of a NumpyTextFileRti

        Inherits from ArrayRti but shows a 'field' glyph as icon to indicate that the underlying
        data is the same as it's parent.

        No dedicated constructor defined (reuses the ArrayRti constructor)
    """
    _defaultIconGlyph = RtiIconFactory.FIELD
    _defaultIconColor = ICON_COLOR_NUMPY


class NumpyTextFileRti(ArrayRti):
    """ Represents a 2D array from a simple text file, imported with numpy.loadtxt.
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
            colItem = NumpyTextColumnRti(self._array[:, col], nodeName="column-{}".format(col),
                                         fileName=self.fileName, iconColor=self.iconColor)
            childItems.append(colItem)
        return childItems
