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

""" Wrappers that offer a uniform interface to variables, groups etc.

    
"""
import numpy as np
from libargos.utils import check_class, StringType
from libargos.qt.editabletreemodel import BaseTreeItem


# TODO: derive from object?

class StoreTreeItem(BaseTreeItem):
    """ Base node from which to derive the other types of nodes.
    
        Serves as an interface but can also be instantiated for debugging purposes.
    
    """
    def __init__(self, parentItem, nodeName=None, nodeId=None):
        """ Constructor
        """
        super(StoreTreeItem, self).__init__(parentItem)
        check_class(nodeName, StringType, allow_none=True) # TODO: allow_none?
        self._nodeName = nodeName
        self._nodeId = nodeId if nodeId is not None else self._nodeName
        
    @property
    def nodeName(self): # TODO: to BaseTreeItem?
        """ The node name."""
        return self._nodeName
        
    @property
    def nodeId(self): # TODO: needed?
        """ The node identifier. Defaults to the name"""
        return self._nodeId
    
    @property
    def attributes(self):
        return {}
    

class StoreGroupTreeItem(StoreTreeItem):
    pass



class StoreScalarTreeItem(BaseTreeItem): # TODO: remove?
    
    def __init__(self, name, value, parentItem=None):
        super(StoreScalarTreeItem, self).__init__(parentItem)
        self.name = name
        self.value = value 


class StoreArrayTreeItem(StoreTreeItem):
    
    def __init__(self, array, parentItem=None, nodeName=None):
        """ Constructor
        """
        super(StoreArrayTreeItem, self).__init__(parentItem=parentItem, nodeName=nodeName)
        check_class(array, np.ndarray)
        self._array = array
   
    @property
    def dimensions(self):
        return []
    
    @property
    def elementType(self):
        return None # Not an array
    
    @property
    def arrayShape(self):
        return self._array.shape
    
    @property
    def arrayElemType(self):
        return self._array.dtype

    