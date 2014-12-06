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

""" Data repository functionality
"""
import logging
from libargos.qt.editabletreemodel import BaseTreeModel
from libargos.info import DEBUGGING
from libargos.utils import check_class, type_name

from .treeitems import BaseRti, LazyLoadRtiMixin


logger = logging.getLogger(__name__)

class RepositoryTreeModel(BaseTreeModel):
    """ The main entry point of all the data
    
        Maintains a list of open files and offers a QAbstractItemModel for read-only access of
        the data with QTreeViews.
    """
    HEADERS = ["name", "shape", "tree item", "type", "elem type", "file name"]
    (COL_NODE_NAME, COL_SHAPE, 
     COL_RTI_TYPE, COL_TYPE, COL_ELEM_TYPE, 
     COL_FILE_NAME) = range(len(HEADERS))
    
    def __init__(self, parent=None):
        """ Constructor
        """
        super(RepositoryTreeModel, self).__init__(parent=parent)
        self._isEditable = False

    
    def _itemValueForColumn(self, treeItem, column):
        """ Returns the value of the item given the column number.
            :rtype: string
        """
        if column == self.COL_NODE_NAME:
            return treeItem.nodeName
        elif column == self.COL_SHAPE:
            return " x ".join(str(elem) for elem in treeItem.arrayShape)
        elif column == self.COL_RTI_TYPE: # repo tree item type
            return type_name(treeItem)
        elif column == self.COL_TYPE:
            return treeItem.typeName
        elif column == self.COL_ELEM_TYPE:
            return treeItem.elementTypeName
        elif column == self.COL_FILE_NAME:
            return treeItem.fileName if hasattr(treeItem, 'fileName') else ''
        else:
            raise ValueError("Invalid column: {}".format(column))
            

    def _setItemValueForColumn(self, treeItem, column, value):
        """ Sets the value in the item, of the item given the column number.
            It returns True for success, otherwise False.
        """
        assert False, "not operational"
        if column == 1:
            treeItem.value = value
            return True
        else:
            if DEBUGGING:
                raise IndexError("Invalid column number: {}".format(column))
            return False
        
        
    def canFetchMore(self, parentIndex):
        """ Returns true if there is more data available for parent; otherwise returns false.
        """
        parentItem = self.getItem(parentIndex)
        if not parentItem:
            return False
        
        return parentItem.canFetchChildren()
        
        
    def fetchMore(self, parentIndex):
        """ Fetches any available data for the items with the parent specified by the parent index.
        """
        parentItem = self.getItem(parentIndex)
        if not parentItem:
            return
        
        if not isinstance(parentItem, LazyLoadRtiMixin):
            return 
        
        if not parentItem.canFetchChildren():
            return
        
        # TODO: implement InsertItems to optimize?
        for childItem in parentItem.fetchChildren(): 
            self.insertItem(childItem, parentIndex=parentIndex)
        
        # Check that Rti implementation correctly sets _canFetchChildren    
        assert not parentItem.canFetchChildren(), "not all children fetched: {}".format(parentItem)

    
   
class Repository(object):
    """ TODO: do we keep this class? It doesn't do much
    """
    
    def __init__(self):
        self._treeModel = RepositoryTreeModel()
        
    
    @property
    def treeModel(self):
        return self._treeModel
        
    
    def appendTreeItem(self, repoTreeItem):
        """ Appends a store to the end of the ordered store dictionary
            
            Returns the index in of the store's root item (so it can be selected).
        """
        check_class(repoTreeItem, BaseRti)
        storeRootIndex = self.treeModel.insertItem(repoTreeItem)
        return storeRootIndex
            
        