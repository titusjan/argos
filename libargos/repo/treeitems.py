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

ICONS_DIRECTORY = os.path.join(program_directory(), 'img/snipicons')

logger = logging.getLogger(__name__)

class BaseRti(BaseTreeItem):
    """ TreeItem for use in a RepositoryTreeModel. (RTI = Repository TreeItem)
        Base node from which to derive the other types of nodes.
        Serves as an interface but can also be instantiated for debugging purposes.
    """
    _icon = None # can be overridden by a QtGui.QIcon
    
    def __init__(self, nodeName=None):
        """ Constructor
        
            :param nodeName: name of this node.
        """
        super(BaseRti, self).__init__()
        check_class(nodeName, StringType, allow_none=False) # TODO: allow_none?
        self._nodeName = str(nodeName)
    
    @property    
    def icon(self):
        return self._icon

    @property
    def nodeName(self): # TODO: to BaseTreeItem?
        """ The node name."""
        return self._nodeName
        
    @property
    def typeName(self):
        return ""
    
    @property                  # TODO: move?
    def elementTypeName(self):
        return ""
    
    @property
    def arrayShape(self):      # TODO: move?
        return tuple()
    
#    @property
#    def dimensions(self):
#        return []
#    
#    @property
#    def attributes(self):
#        return {}

class VisDataRti(BaseRti):
    """ TreeItem that is can do lazy loading of children by implementing the fetchChildren method.
        It is generally a leaf in the repository.
    """
    pass # TODO: implement?
            
    
class LazyLoadRtiMixin(object):
    """ Rti that can do lazy loading of children by implementing the fetchChildren method.
    """
    def __init__(self, nodeName=None):
        """ Constructor
        """
        self._childrenFetched = False
        
    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children 
        """
        return not self._childrenFetched or len(self.childItems) > 0
        
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
        
        

class FileRtiMixin(object): 
    """ A BaseRti that opens a file and maintains a reference to it.
    """
    def __init__(self, fileName):
        """ Constructor """
        #fileName = os.path.normpath(fileName) # realpath?
        fileName = os.path.realpath(fileName) 
        assert os.path.exists(fileName), "File not found: {}".format(fileName)
        self._fileName = fileName
        
    @property
    def fileName(self):
        """ Returns the name of the underlying the file. 
        """
        return self._fileName
    
    def closeFile(self):
        """ Closes the underlying file. 
            Should be called before removing this item from the repository.
        """
        raise NotImplementedError("Descendants must implement closeFile")
        
    @classmethod
    def createFromFileName(cls, fileName):
        """ Creates a FileRtiMixin (or descendant), given a file name.
        """
        # See https://julien.danjou.info/blog/2013/guide-python-static-class-abstract-methods
        return cls(fileName, nodeName=os.path.basename(fileName))

    
    