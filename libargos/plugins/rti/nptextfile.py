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
from libargos.repo.memoryrti import ArrayRti
from libargos.repo.treeitems import ICONS_DIRECTORY, LazyLoadRtiMixin, FileRtiMixin

logger = logging.getLogger(__name__)

_ICOLOR = 'FF00FF' 



class NumpyTextColumnRti(ArrayRti):
    """ Represents a column from a simple text file, imported with numpy.loadtxt. 
    """
    _icon = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'th-large.{}.svg'.format(_ICOLOR)))
    

class NumpyTextFileRti(LazyLoadRtiMixin, FileRtiMixin, ArrayRti):
    """ Represents a 2D array from a simple text file, imported with numpy.loadtxt.
    """
    _icon = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'file.{}.svg'.format(_ICOLOR)))
        
    def __init__(self, fileName, nodeName=None):
        LazyLoadRtiMixin.__init__(self) 
        FileRtiMixin.__init__(self, fileName) 
        ArrayRti.__init__(self, np.loadtxt(self.fileName, ndmin=0), nodeName=nodeName)
        
    
    def closeFile(self):
        """ Does nothing since the underlying file is already closed during _fetchAllChildren
        """
        pass
            
        
    def _fetchAllChildren(self):
        """ Walks through all items and returns node to fill the repository
        """
        childItems = []
        _nRows, nCols = self._array.shape
        for col in range(nCols):
            colItem = NumpyTextColumnRti(self._array[:, col], nodeName="column {}".format(col))
            childItems.append(colItem)
        return childItems
