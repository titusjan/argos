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
    _iconOpen = None   # can be overridden by a QtGui.QIcon
    _iconClosed = None # can be overridden by a QtGui.QIcon
    _iconError = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'err.warning.svg'))    
    #_iconError = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, 'err.exclamation.svg'))    
    
    def __init__(self, nodeName, fileName=''):
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

#    @classmethod # TODO: obsolete?
#    def classLabel(cls):
#        """ Returns a short string that describes this class. For use in menus, headers, etc. 
#        """
#        return cls._label
    
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
        self.clearException()
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
            self.setException(ex)
            
        
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
        self.clearException()
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
            self.setException(ex)

            
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
            self.setException(IOError(msg))
            return False
        else:
            return True
        
    @property
    def exception(self):
        """ The exception if an error has occurred during reading
        """
        return self._exception
    

    def setException(self, ex):
        """ Sets the exception attribute.
        """
        self._exception = ex

        
    def clearException(self):
        """ Forgets any stored exception to clear the possible error icon
        """
        self._exception = None    
        
    
    def fetchChildren(self):
        """ Creates child items and returns them. 
            Opens the tree item first if it's not yet open.
        """
        assert not self._childrenFetched, "canFetchChildren must be True"
        self.clearException()

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
            self.setException(ex)
        
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
    def decoration(self):
        """ The displayed icon.
         
            Shows open icon when node was visited (children are fetched). This allows users
            for instance to collapse a directory node but still see that it was visited, which
            may be useful if there is a huge list of directories.
        """
        if self._exception:
            return self._iconError
        elif self._childrenFetched:
            return self._iconOpen
        else:
            return self._iconClosed

    
    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return ""

    
    @property
    def isSliceable(self):
        """ Returns True if the underlying data can be sliced.
            You should always check this before using an index/slice on an RTI.
        """
        return self._asArray is not None
    
    
    @property
    def _asArray(self):
        """ Returns the underlying data as an array-like object that supports multi-dimensional 
            indexing and other methods of numpy arrays (e.g. the shape). It can, for instance, 
            return a h5py dataset. 
            
            If the underlying data cannot be represented as an array, this property returns None.
            Note that the implementation is expected to be fast; it should not retrieve actual 
            array data from an underlying file, only return a reference.
        """
        return None
        
    
    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]). 
            Passes the index through to the underlying array.
        """
        return self._asArray.__getitem__(index)
        
                
    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array. Returns an empty tuple if the underlying
            array is None.
            Raised TypeError if the RTI is not sliceable
        """
        if self.isSliceable:
            return self._asArray.shape
        else:
            raise TypeError("RTI is not sliceable: {}".format(self))
        
        #return tuple() if not self.isSliceable is None else self._asArray.shape
        
    
    @property
    def nDims(self):
        """ The number of dimension of the underlying array
            Should return 0 for scalars.
        """
        return len(self.arrayShape)
    
#    @property
#    def dimensions(self):
#        return []
#    
    @property
    def attributes(self):
        """ The attribute dictionary. 
            The attributes generally contain meta data about the item. 
        """
        return {}


    
    