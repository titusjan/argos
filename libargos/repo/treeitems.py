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

""" Repository TreeItem (RTI) classes
    Tree items for use in the RepositoryTreeModel
"""
import logging, os

from libargos.info import program_directory
from libargos.qt.editabletreemodel import BaseTreeItem
from libargos.utils.cls import StringType, check_class

ICONS_DIRECTORY = os.path.join(program_directory(), 'img/icons')

logger = logging.getLogger(__name__)


    
class _LazyLoadRtiMixin(object):
    """ Mixing for a tree item that can do lazy loading of children by implementing 
        the fetchChildren method.
    """
    def __init__(self):
        """ Constructor
        """
        self._childrenFetched = False
        
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return True
        #return not self._childrenFetched or len(self.childItems) > 0 TODO: use this? 
        
    def canFetchChildren(self):
        return not self._childrenFetched
        
    def fetchChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"
        childItems = self._fetchAllChildren()
        self._childrenFetched = True
        return childItems
    
    def _fetchAllChildren(self):
        """ The function that actually fetches the children.
            The result must be a list of RepoTreeItems. Their parents must be None, 
            it will be set by BaseTreeitem.insertItem()
         
            :rtype: list of BaseRti objects
        """ 
        raise NotImplementedError
        
    def setUnfetched(self):
        self._childrenFetched = False
        

class _FileRtiMixin(object): 
    """ A mixin for an Rti that opens a file and maintains a reference to it.
        It defines the createFromFileName factory. 
    """
    def __init__(self, fileName):
        """ Constructor """
        check_class(fileName, StringType, allow_none=True) 
        if fileName:
            fileName = os.path.realpath(fileName) 
            assert os.path.exists(fileName), "File not found: {}".format(fileName)
        self._fileName = fileName
        
        
    @property
    def fileName(self):
        """ Returns the name of the underlying the file. 
        """
        return self._fileName
            
    @classmethod
    def createFromFileName(cls, fileName):
        """ Creates a FileRtiMixin (or descendant), given a file name.
        """
        # See https://julien.danjou.info/blog/2013/guide-python-static-class-abstract-methods
        #logger.debug("Trying to create object of class: {!r}".format(cls))
        return cls(nodeName=os.path.basename(fileName), fileName=fileName)
    
    

class BaseRti( _FileRtiMixin, _LazyLoadRtiMixin, BaseTreeItem):
    """ TreeItem for use in a RepositoryTreeModel. (RTI = Repository TreeItem)
        Base node from which to derive the other types of nodes.
        Serves as an interface but can also be instantiated for debugging purposes.
    """
    _iconOpen = None   # can be overridden by a QtGui.QIcon
    _iconClosed = None # can be overridden by a QtGui.QIcon
    
    def __init__(self, nodeName='', fileName=''):
        """ Constructor
        
            :param nodeName: name of this node.
        """
        BaseTreeItem.__init__(self)
        _LazyLoadRtiMixin.__init__(self) 
        _FileRtiMixin.__init__(self, fileName) 
        print (self._childItems)
        #_LazyLoadRtiMixin.__init__(self) 
        #_FileRtiMixin.__init__(self, fileName) 
        #BaseTreeItem.__init__(self)
        check_class(nodeName, StringType, allow_none=False) # TODO: allow_none?
        self._nodeName = str(nodeName)
        self._isOpen = False

    @property
    def isOpen(self):
        "Returns True if the underlying resources are opened"
        return self._isOpen
    
    
    def open(self):
        """ Opens underlying resources and sets isOpen flag. 
            It calls _openResources. Descendants should usually override the latter 
            function instead of this one.
        """
        logger.debug("Opening {}".format(self))        
        if self._isOpen:
            logger.warn("Resources already open. Closing them first.")
            self.close()
        self._openResources()
        self._isOpen = True
        
    def _openResources(self):
        """ Can be overridden to open the underlying resources. 
            The default implementation does nothing.
            Is called by self.open
        """
        pass
    
    def close(self):
        """ Opens underlying resources and unsets isOpen flag. 
            It calls _closeResources. Descendants should usually override the latter 
            function instead of this one.
        """
        logger.debug("Closing {}".format(self))        
        if self._isOpen:
            self._closeResources()
        self._isOpen = False
            
    def _closeResources(self):
        """ Can be overridden to close the underlying resources. 
            The default implementation does nothing.
            Is called by self.close
        """
        pass

    
    def _fetchAllChildren(self):
        """ The function that actually fetches the children. Default returns no children.
        """ 
        return []
    
    def removeAllChildren(self):
        BaseTreeItem.removeAllChildren(self)
        self.setUnfetched()
        
    def finalize(self):
        """ Can be used to cleanup resources. Should be called explicitly.
            Finalizes its children before closing itself
        """
        for child in self.childItems:
            child.finalize()
        self.close()

    @property
    def icon(self):
        "Icon displayed. Shows open icon when node was visited (children are fetched)"
        if self._childrenFetched: # a bit of an experiment
            return self._iconOpen
        else:
            return self._iconClosed
            
    @property
    def nodeName(self): # TODO: to BaseTreeItem?
        """ The node name."""
        return self._nodeName
        
    @property
    def typeName(self):
        return ""
    
    @property
    def elementTypeName(self):
        return ""
    
    @property
    def arrayShape(self):
        return tuple()
    
#    @property
#    def dimensions(self):
#        return []
#    
#    @property
#    def attributes(self):
#        return {}


    
    