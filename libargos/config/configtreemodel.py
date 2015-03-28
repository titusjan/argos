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
from libargos.qt import QtCore, QtSlot
from libargos.qt.treemodels import BaseTreeModel
from libargos.info import DEBUGGING
from libargos.utils.cls import type_name


logger = logging.getLogger(__name__)

class ConfigTreeModel(BaseTreeModel):
    """ An implementation QAbstractItemModel that offers access to configuration data for QTreeViews. 
        The underlying data is stored as config tree items (BaseCti descendants)
    """    
    HEADERS = ["name", "path", "value", "default value", "tree item", "debug info"]
    (COL_NODE_NAME, COL_NODE_PATH, 
     COL_VALUE, COL_DEF_VALUE, 
     COL_CTI_TYPE, COL_DEBUG) = range(len(HEADERS))
    
    def __init__(self, parent=None):
        """ Constructor
        """
        super(ConfigTreeModel, self).__init__(parent=parent)
        
        self.dataChanged.connect(self.debug)


    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def debug(self, topLeftIndex, bottomRightIndex):
        """ Temporary debug to test the dataChanged signal
        """
        topRow = topLeftIndex.row()
        bottomRow = bottomRightIndex.row()
        
        for row in range(topRow, bottomRow + 1):
            index = topLeftIndex.sibling(row, 0)
            childItem = self.getItem(index)
            logger.debug("Data changed in: {}".format(childItem.nodePath))

        
    def flags(self, index):
        """ Returns the item flags for the given index.
        """
        if not index.isValid():
            return 0
        
        result = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable 

        if index.column() == self.COL_VALUE:   
            result |= QtCore.Qt.ItemIsEditable
            
        return result
        
    
    def _displayValueForColumn(self, treeItem, column):
        """ Returns the display value of the item given the column number.
            :rtype: string
        """
        if column == self.COL_NODE_NAME:
            return treeItem.nodeName
        elif column == self.COL_NODE_PATH:
            return treeItem.nodePath
        elif column == self.COL_VALUE:
            return treeItem.displayValue
        elif column == self.COL_DEF_VALUE:
            return str(treeItem.defaultValue)
        elif column == self.COL_CTI_TYPE:
            return type_name(treeItem)
        elif column == self.COL_DEBUG:
            return treeItem.debugInfo
        else:
            raise ValueError("Invalid column: {}".format(column))
        
    
    def _editValueForColumn(self, treeItem, column):
        """ Returns the value for editing of the item given the column number.
            :rtype: string
        """
        if column == self.COL_VALUE:
            return treeItem.value
        else:
            raise ValueError("Invalid column: {}".format(column))
            

    def _setEditValueForColumn(self, treeItem, column, value):
        """ Sets the value in the item, of the item given the column number.
            It returns True for success, otherwise False.
        """
        if column != self.COL_VALUE:
            return False
        try:
            treeItem.value = value
        except Exception:
            raise
        else:
            return True
        

    
