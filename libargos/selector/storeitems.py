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
import logging

from libargos.utils import (StringType, check_class, 
                            check_is_a_sequence, check_is_a_mapping, check_is_an_array,  
                            is_a_sequence, is_a_mapping, is_an_array, type_name)
from libargos.qt.editabletreemodel import BaseTreeItem


logger = logging.getLogger(__name__)

class StoreTreeItem(BaseTreeItem):
    """ Base node from which to derive the other types of nodes.
    
        Serves as an interface but can also be instantiated for debugging purposes.
    
    """
    def __init__(self, parentItem=None, nodeName=None, nodeId=None):
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
    
    def canFetchChildren(self):
        return False
    
    def fetchChildren(self):
        return []

    @staticmethod
    def createFromObject(nodeName, obj):
        if is_a_sequence(obj):
            return SequenceStoreTreeItem(nodeName, obj)
        elif is_a_mapping(obj):
            return MappingStoreTreeItem(nodeName, obj)
        elif is_an_array(obj):
            return ArrayStoreTreeItem(nodeName, obj)
        else:
            return ScalarStoreTreeItem(nodeName, obj)
        
    
class GroupStoreTreeItem(StoreTreeItem):

    def __init__(self, parentItem=None, nodeName=None, nodeId=None):
        """ Constructor
        """
        super(GroupStoreTreeItem, self).__init__(parentItem, nodeName = nodeName)
        self._childrenFetched = False
        
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        logger.debug("{} has children = {}".format(self, not self._childrenFetched or len(self.childItems) > 0))
        return not self._childrenFetched or len(self.childItems) > 0
        
    def canFetchChildren(self):
        return not self._childrenFetched
        
    def fetchChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"

        # When overriding, put your code here. Keep the other lines.        
        childItems = [] 
        # childItems must be a list of StoreTreeItems. Their parent must be None, it
        # will be set by BaseTreeitem.insertItem()
        
        self._childrenFetched = True
        return childItems
    
    

class ScalarStoreTreeItem(StoreTreeItem):
    """ Stores a Python or numpy scalar
    """
    def __init__(self, nodeName, scalar, parentItem=None):
        super(ScalarStoreTreeItem, self).__init__(parentItem, nodeName = nodeName)
        self._scalar = scalar 
    
    @property
    def typeName(self):
        return type_name(self._scalar)
    
    @property
    def elementTypeName(self):
        return self.typeName
    

class ArrayStoreTreeItem(StoreTreeItem):
    
    def __init__(self, nodeName, array, parentItem=None):
        """ Constructor
        """
        super(ArrayStoreTreeItem, self).__init__(parentItem=parentItem, nodeName=nodeName)
        check_is_an_array(array)
        self._array = array
   
    @property
    def arrayShape(self):
        return self._array.shape

    @property
    def typeName(self):
        return type_name(self._array)
    
    @property
    def elementTypeName(self):
        dtype =  self._array.dtype
        return '<compound>' if dtype.names else str(dtype)
    

class SequenceStoreTreeItem(GroupStoreTreeItem):
    
    def __init__(self, nodeName, sequence, parentItem=None):
        """ Constructor
        """
        super(SequenceStoreTreeItem, self).__init__(parentItem=parentItem, nodeName=nodeName)
        check_is_a_sequence(sequence)
        self._sequence = sequence
   
    @property
    def arrayShape(self):
        return (len(self._sequence), )

    @property
    def typeName(self):
        return type_name(self._sequence)
    
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return len(self._sequence) > 0
        
    def fetchChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"
        childItems = []
        for nr, elem in enumerate(self._sequence):
            childItems.append(self.createFromObject("elem-{}".format(nr), elem))

        self._childrenFetched = True
        return childItems
    


class MappingStoreTreeItem(GroupStoreTreeItem):
    
    def __init__(self, nodeName, dictionary, parentItem=None, ):
        """ Constructor
        """
        super(MappingStoreTreeItem, self).__init__(parentItem=parentItem, nodeName=nodeName)
        check_is_a_mapping(dictionary)
        self._dictionary = dictionary

    @property
    def arrayShape(self):
        return (len(self._dictionary), )

    @property
    def typeName(self):
        return type_name(self._dictionary)
    
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return len(self._dictionary) > 0
        
    def fetchChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"
        childItems = []
        for key, value in sorted(self._dictionary.items()):
            #logger.debug("appending: {} -> {!r}".format(key, value))
            childItems.append(self.createFromObject(str(key), value))
            
        self._childrenFetched = True
        return childItems


    