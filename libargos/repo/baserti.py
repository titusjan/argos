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
from libargos.qt import QtGui # TODO: get rid of dependency on QtGui?
from libargos.qt.treeitems import AbstractLazyLoadTreeItem
from libargos.utils.cls import StringType, check_class, is_a_sequence

ICONS_DIRECTORY = os.path.join(program_directory(), 'img/icons')

logger = logging.getLogger(__name__)


class BaseRti(AbstractLazyLoadTreeItem):
    """ TreeItem for use in a RepositoryTreeModel. (RTI = Repository TreeItem)
        Base node from which to derive the other types of nodes.

        Serves as an interface but can also be instantiated for debugging purposes.
    """
    _label = "Unknown Item"
    _iconOpen = None   # can be overridden by a QtGui.QIcon
    _iconClosed = None # can be overridden by a QtGui.QIcon
    _iconError = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'err.warning.svg'))    
    #_iconError = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'err.exclamation.svg'))    
    
    def __init__(self, nodeName='', fileName=''):
        """ Constructor
        
            :param nodeName: name of this node (used to construct the node path).
            :param fileName: absolute path to the file where the data of this RTI originates.
        """
        super(BaseRti, self).__init__(nodeName=nodeName)

        self._isOpen = False
        self._exception = None # Any exception that may occur when opening this item. 
        
        check_class(fileName, StringType, allow_none=True) 
        if fileName:
            fileName = os.path.realpath(fileName) 
        self._fileName = fileName
    
                
    @classmethod
    def createFromFileName(cls, fileName):
        """ Creates a BaseRti (or descendant), given a file name.
        """
        # See https://julien.danjou.info/blog/2013/guide-python-static-class-abstract-methods
        #logger.debug("Trying to create object of class: {!r}".format(cls))
        return cls(nodeName=os.path.basename(fileName), fileName=fileName)

    @classmethod
    def classLabel(cls):
        """ Returns a short string that describes this class. For use in menus, headers, etc. 
        """
        return cls._label
    
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
        self._clearException()
        try:
            if self._isOpen:
                logger.warn("Resources already open. Closing them first before opening.")
                self._closeResources()
                self._isOpen = False
            
            assert not self._isOpen, "Sanity check failed: _isOpen should be false"
            logger.debug("Opening {}".format(self))
            self._openResources()
            self._isOpen = True
            
        except Exception as ex:
            if DEBUGGING:
                raise            
            logger.error("Error during tree item open: {}".format(ex))
            self._setException(ex)
            
        
    def _openResources(self):
        """ Can be overridden to open the underlying resources. 
            The default implementation does nothing.
            Is called by self.open
        """
        pass
    
    
    def close(self):
        """ Closes underlying resources and un-sets isOpen flag. 
            It calls _closeResources. Descendants should usually override the latter 
            function instead of this one.
        """
        self._clearException()
        try: 
            if self._isOpen:
                logger.debug("Closing {}".format(self))        
                self._closeResources()
                self._isOpen = False 
            else:
                logger.debug("Resources already closed (ignored): {}".format(self))
        except Exception as ex:
            if DEBUGGING:
                raise
            logger.error("Error during tree item close: {}".format(ex))
            self._setException(ex)

            
    def _closeResources(self):
        """ Can be overridden to close the underlying resources. 
            The default implementation does nothing.
            Is called by self.close
        """
        pass
    
    
    def _checkFileExists(self):
        """ Verifies that the underlying file exists and sets the _exception attribute if not
            Returns True if the file exists.
            If self._fileName is None, nothing is checked and True is returned.
        """
        if self._fileName and not os.path.exists(self._fileName):
            msg = "File not found: {}".format(self._fileName)
            logger.error(msg)
            self._setException(IOError(msg))
            return False
        else:
            return True
        
        
    def _setException(self, ex):
        """ Sets the exception attribute
        """
        self._exception = ex

        
    def _clearException(self):
        """ Forgets any stored exception to clear the possible error icon
        """
        self._exception = None    
        
    
    def fetchChildren(self):
        """ Creates child items and returns them. 
            Opens the tree item first if it's not yet open.
        """
        assert not self._childrenFetched, "canFetchChildren must be True"
        self._clearException()

        if not self.isOpen:
            self.open()
        
        if not self.isOpen:
            logger.warn("Opening item failed during fetch (aborted)")
            self._childrenFetched = True
            return [] # no need to continue if opening failed.
        
        childItems = []
        try:
            childItems = self._fetchAllChildren()
            assert is_a_sequence(childItems), "ChildItems must be a sequence"    
            self._childrenFetched = True
            
        except Exception as ex:
            # This can happen, for example, when a NCDF/HDF5 file contains data types that
            # are not supported by the Python library that is used to read them.
            if DEBUGGING:
                raise
            logger.error("Unable fetch tree item children: {}".format(ex))
            self._setException(ex)
        
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
    @property
    def attributes(self):
        return {}


    
    