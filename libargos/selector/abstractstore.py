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
import logging

from libargos.qt.editabletreemodel import BaseTreeItem
from libargos.utils import StringType, check_class

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

        
    
class GroupStoreTreeItem(StoreTreeItem):

    def __init__(self, parentItem=None, nodeName=None, nodeId=None):
        """ Constructor
        """
        super(GroupStoreTreeItem, self).__init__(parentItem, nodeName = nodeName)
        self._childrenFetched = False
        
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
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
    
        

class AbstractStore(object):
    
    def open(self, fileName):
        pass
    
    def close(self):
        pass
    
    def createItems(self):
        """ Walks through all items and returns node to fill the repository
        """
        pass
    
    