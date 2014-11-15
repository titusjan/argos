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
logger = logging.getLogger(__name__)


from libargos.selector.abstractstore import AbstractStore, GroupStoreTreeItem
from libargos.selector.memorystore import ArrayStoreTreeItem


class SimpleTextFileStore(AbstractStore):
    """ Store for representing data that is read from a simple text file.
    """
    def __init__(self, fileName):
        self._fileName = fileName
        self._data2D = None
    
    def open(self):
        self._data2D = np.loadtxt(self.fileName, ndmin=0)
    
    def close(self):
        self._data2D = None
        
    @property
    def fileName(self):
        return self._fileName
    
    def createItems(self):
        """ Walks through all items and returns node to fill the repository
        """
        assert self._data2D is not None, "File not opened: {}".format(self.fileName)
        
        fileRootItem = GroupStoreTreeItem(parentItem=None, 
                                          nodeName=os.path.basename(self.fileName), 
                                          nodeId=self.fileName)
        _nRows, nCols = self._data2D.shape
        for col in range(nCols):
            nodeName="column {}".format(col)
            colItem = ArrayStoreTreeItem(nodeName, self._data2D[:,col])
            fileRootItem.insertChild(colItem)
            
        return fileRootItem


