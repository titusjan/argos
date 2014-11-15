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

""" Store and Tree items for representing data that is stored in memory.
"""
import logging

logger = logging.getLogger(__name__)

from libargos.selector.abstractstore import AbstractStore, StoreTreeItem, GroupStoreTreeItem

from libargos.utils import (check_is_a_sequence, check_is_a_mapping, check_is_an_array,  
                            is_a_sequence, is_a_mapping, is_an_array, type_name)


def _createFromObject(nodeName, obj):
    if is_a_sequence(obj):
        return SequenceStoreTreeItem(nodeName, obj)
    elif is_a_mapping(obj):
        return MappingStoreTreeItem(nodeName, obj)
    elif is_an_array(obj):
        return ArrayStoreTreeItem(nodeName, obj)
    else:
        return ScalarStoreTreeItem(nodeName, obj)
    

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
            childItems.append(_createFromObject("elem-{}".format(nr), elem))

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
            childItems.append(_createFromObject(str(key), value))
            
        self._childrenFetched = True
        return childItems



class MappingStore(AbstractStore):
    """ Stores a dictionary with variables (e.g. the local scope)
    """

    def __init__(self, dictName, dictionary):
        super(MappingStore, self).__init__(dictName) # use the dictName as storeId
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
        