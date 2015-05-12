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

from json import dumps, loads

from libargos.qt import Qt, QtCore, QtSlot
from libargos.qt.treemodels import BaseTreeModel
from libargos.config.basecti import BaseCti
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
        self._rootItem = BaseCti(nodeName='<invisible-root>')
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
        
        result = Qt.ItemIsEnabled | Qt.ItemIsSelectable 

        if index.column() == self.COL_VALUE:   
            result |= Qt.ItemIsEditable
            
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
            return treeItem.data
        else:
            raise ValueError("Invalid column: {}".format(column))
            

    def _setEditValueForColumn(self, treeItem, column, value):
        """ Sets the value in the item, of the item given the column number.
            It returns True for success, otherwise False.
        """
        if column != self.COL_VALUE:
            return False
        try:
            logger.debug("_setEditValueForColumn: {!r}".format(value))
            treeItem.data = value
        except Exception:
            raise
        else:
            return True
        
        
    def readModelSettings(self, key, settings):
        """ Reads the persistent program settings.
        
            Will reset the model and thus collapse all nodes.
            
            :param key: key where the setting will be read from
            :param settings: optional QSettings object which can have a group already opened.
            :returns: True if the header state was restored, otherwise returns False
        """ 
        if settings is None:
            settings = QtCore.QSettings()     
            
        values_json = settings.value(key, None)
        
        if values_json:
            values = loads(values_json)
            self.beginResetModel()
            self.rootItem.setValuesFromDict(values)
            self.endResetModel()
        else:
            logger.warn("No settings found at: {}".format(key))
    

    def saveProfile(self, key, settings=None):
        """ Writes the view settings to the persistent store
            :param key: key where the setting will be read from
            :param settings: optional QSettings object which can have a group already opened.        
        """         
        logger.debug("Writing model settings for: {}".format(key))
        if settings is None:
            settings = QtCore.QSettings()
            
        values = self.rootItem.getNonDefaultsDict()
        values_json = dumps(values)
        settings.setValue(key, values_json)

