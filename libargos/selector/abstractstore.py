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

""" Data stores for use in the Repository

"""
import logging, os
import numpy as np

from libargos.utils import check_is_a_mapping
from libargos.selector.storeitems import (GroupStoreTreeItem, ArrayStoreTreeItem, 
                                          MappingStoreTreeItem)

logger = logging.getLogger(__name__)


class AbstractStore(object):
    
    def open(self, fileName):
        pass
    
    def close(self):
        pass
    
    def createItems(self):
        """ Walks through all items and returns node to fill the repository
        """
        pass


class MappingStore(AbstractStore):
    """ Stores a dictionary with variables (e.g. the local scope)
    """

    def __init__(self, dictName, dictionary):
        check_is_a_mapping(dictionary)
        self._dictionary = dictionary
        self._dictName = dictName
    
    def open(self):
        pass
    
    def close(self):
        pass
    
    def createItems(self):
        """ Walks through all items and returns node to fill the repository
        """
        rootItem = MappingStoreTreeItem(self._dictName, self._dictionary)
        return rootItem


class SimpleTextFileStore(AbstractStore):
    """ 
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
            fileRootItem.insertItem(colItem)
            
        return fileRootItem


    
    