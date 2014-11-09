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

""" Tree items (derived from BaseTreeItem) that store information for in a 
    data store in a repository. 

"""
import numpy as np
from libargos.utils import check_class, check_is_a_sequence, StringType
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
    def typeName(self):
        return ""
    
    @property
    def elementTypeName(self):
        return ""
    
    @property
    def arrayShape(self):
        return tuple()
    
    @property
    def dimensions(self):
        return []
    
    @property
    def attributes(self):
        return {}
    

class StoreGroupTreeItem(StoreTreeItem):
    pass



class StoreScalarTreeItem(StoreTreeItem):
    """ Stores a Python or numpy scalar
    """
    def __init__(self, nodeName, scalar, parentItem=None):
        super(StoreScalarTreeItem, self).__init__(parentItem, nodeName = nodeName)
        self._scalar = scalar 
    
    @property
    def typeName(self):
        return type(self._scalar).__name__
    
    @property
    def elementTypeName(self):
        return self.typeName
    

class StoreArrayTreeItem(StoreTreeItem):
    
    def __init__(self, nodeName, array, parentItem=None):
        """ Constructor
        """
        super(StoreArrayTreeItem, self).__init__(parentItem=parentItem, nodeName=nodeName)
        check_class(array, np.ndarray)
        self._array = array
   
    @property
    def arrayShape(self):
        return self._array.shape

    @property
    def typeName(self):
        return type(self._array).__name__
    
    @property
    def elementTypeName(self):
        return self._array.dtype.name
    

class StoreSequenceTreeItem(StoreTreeItem):
    
    def __init__(self, nodeName, sequence, parentItem=None):
        """ Constructor
        """
        super(StoreSequenceTreeItem, self).__init__(parentItem=parentItem, nodeName=nodeName)
        check_is_a_sequence(check_is_a_sequence)
        self._sequence = sequence
   
    @property
    def arrayShape(self):
        return len(self._sequence)

    @property
    def typeName(self):
        return type(self._sequence)
    


class StoreMapTreeItem(StoreTreeItem):
    
    def __init__(self, nodeName, dictionary, parentItem=None, ):
        """ Constructor
        """
        super(StoreArrayTreeItem, self).__init__(parentItem=parentItem, nodeName=nodeName)
        check_class(dictionary, dict) # TODO: ordered dict?
        self._dictionary = dictionary

    @property
    def arrayShape(self):
        return len(self._dictionary)

    @property
    def typeName(self):
        return type(self._dictionary)
    
    