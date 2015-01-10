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

from libargos.info import program_directory, DEBUGGING
from libargos.qt import QtGui # TODO: get rid of dependency on QtGui
from libargos.qt.editabletreemodel import AbstractLazyLoadTreeItem
from libargos.utils.cls import StringType, check_class

ICONS_DIRECTORY = os.path.join(program_directory(), 'img/icons')

logger = logging.getLogger(__name__)


class BaseRti(AbstractLazyLoadTreeItem):
    """ TreeItem for use in a RepositoryTreeModel. (RTI = Repository TreeItem)
        Base node from which to derive the other types of nodes.

        Serves as an interface but can also be instantiated for debugging purposes.
    """
    _iconOpen = None   # can be overridden by a QtGui.QIcon
    _iconClosed = None # can be overridden by a QtGui.QIcon
    _iconError = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'err.warning.svg'))    
    #_iconError = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'err.exclamation.svg'))    
    
    def __init__(self, nodeName='', fileName=''):
        """ Constructor
        
            :param nodeName: name of this node (used to construct the node path).
            :param fileName: absolute path to the file where the data of this RTI originates.
        """
        super(BaseRti, self).__init__()
        
        check_class(nodeName, StringType, allow_none=False) # TODO: allow_none?
        self._nodeName = str(nodeName)
        self._isOpen = False
        self._exception = None # Any exception that may occur when opening this item. 
        
        check_class(fileName, StringType, allow_none=True) 
        if fileName:
            fileName = os.path.realpath(fileName) 
            assert os.path.exists(fileName), "File not found: {}".format(fileName)
        self._fileName = fileName
    
                
    @classmethod
    def createFromFileName(cls, fileName):
        """ Creates a BaseRti (or descendant), given a file name.
        """
        # See https://julien.danjou.info/blog/2013/guide-python-static-class-abstract-methods
        #logger.debug("Trying to create object of class: {!r}".format(cls))
        return cls(nodeName=os.path.basename(fileName), fileName=fileName)
    
    @property
    def fileName(self):
        """ Returns the name of the underlying the file. 
        """
        return self._fileName
            
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
        self._forgetException()        
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
    
    def _forgetException(self):
        """ Forgets any stored exception to clear the possible error icon
        """
        self._exception = None    
        
    
    def fetchChildren(self):
        assert self.canFetchChildren(), "canFetchChildren must be True"
        try:
            childItems = self._fetchAllChildren()
        except Exception as ex:
            if DEBUGGING:
                raise
            # This can happen, for example, when an RTI tries to open the underlying file 
            # when expanding and the underlying file is not of the expected format.
            childItems = []
            self._exception = ex
            logger.error("Unable get children of {}".format(self))
            logger.error("Reason: {}".format(ex))
            
        self._childrenFetched = True
        return childItems    

    
    def _fetchAllChildren(self):
        """ The function that actually fetches the children. Default returns no children.
        """ 
        return []

        
    def finalize(self):
        """ Can be used to cleanup resources. Should be called explicitly.
            Finalizes its children before closing itself
        """
        for child in self.childItems:
            child.finalize()
        self.close()

    @property
    def icon(self):
        """ The displayed icon.
         
            Shows open icon when node was visited (children are fetched). This allows users
            for instance to collapse a directory node but still see that it was visited, whic
            may be useful if there is a huge list of directories.
        """
        if self._exception:
            return self._iconError
        elif self._childrenFetched:
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


    
    