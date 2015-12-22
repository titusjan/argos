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

from libargos.qt import Qt, QtCore, QtSlot
from libargos.qt.treemodels import BaseTreeModel
from libargos.config.abstractcti import ctiDumps, ctiLoads
from libargos.config.groupcti import GroupCti
from libargos.utils.cls import type_name


logger = logging.getLogger(__name__)

class ConfigTreeModel(BaseTreeModel):
    """ An implementation QAbstractItemModel that offers access to configuration data for QTreeViews. 
        The underlying data is stored as config tree items (AbstractCti descendants)
    """    
    HEADERS = ["name", "path", "value", "default value", "tree item", "debug info"]
    (COL_NODE_NAME, COL_NODE_PATH, 
     COL_VALUE, COL_DEF_VALUE, 
     COL_CTI_TYPE, COL_DEBUG) = range(len(HEADERS))
     
    COL_DECORATION = COL_VALUE   # Column number that contains the decoration.
    
    def __init__(self, parent=None):
        """ Constructor
        """
        super(ConfigTreeModel, self).__init__(parent=parent)
        self._invisibleRootItem = GroupCti('<invisible-root>')
        self.dataChanged.connect(self.debug)


    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def debug(self, topLeftIndex, bottomRightIndex):
        """ Temporary debug to test the dataChanged signal
        """
        if topLeftIndex.isValid() and bottomRightIndex.isValid():
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
        
        cti = self.getItem(index)  
        
        result = Qt.ItemIsSelectable
        
        if cti.enabled:
            result |= Qt.ItemIsEnabled

        if index.column() == self.COL_VALUE: 
            result |= cti.valueColumnItemFlags
            
        return result
        
    
    def displayValueForColumn(self, treeItem, column):
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
            return treeItem.displayDefaultValue
        elif column == self.COL_CTI_TYPE:
            return type_name(treeItem)
        elif column == self.COL_DEBUG:
            return treeItem.debugInfo
        else:
            raise ValueError("Invalid column: {}".format(column))
        
    
    def editValueForColumn(self, treeItem, column):
        """ Returns the value for editing of the item given the column number.
            :rtype: string
        """
        if column == self.COL_VALUE:
            return treeItem.data
        else:
            raise ValueError("Invalid column: {}".format(column))
            

    def setEditValueForColumn(self, treeItem, column, value):
        """ Sets the value in the item, of the item given the column number.
            It returns True for success, otherwise False.
        """
        if column != self.COL_VALUE:
            return False
        try:
            logger.debug("setEditValueForColumn: {!r}".format(value))
            treeItem.data = value
        except Exception:
            raise
        else:
            return True
        

    def checkStateForColumn(self, treeItem, column):
        """ Returns the check state of the item given the column number.
            for the given column number.
            :rtype: Qt.CheckState or None
        """
        if column != self.COL_VALUE:
            # The CheckStateRole is called for each cell so return None here.              
            return None
        else:
            return treeItem.checkState
            
            
    def setCheckStateForColumn(self, treeItem, column, checkState):
        """ Sets the check state in the item, of the item given the column number.
            It returns True for success, otherwise False.
        """
        if column != self.COL_VALUE:
            return False
        else:
            logger.debug("setCheckStateForColumn: {!r}".format(checkState))
            try:
                treeItem.checkState = checkState
            except NotImplementedError:
                return False
            else:
                return True
            
            
    def setExpanded(self, index, expanded):
        """ Expands the model item specified by the index.
            Overridden from QTreeView to make it persistent (between inspector changes).
        """
        if index.isValid():
            item = self.getItem(index)
            item.expanded = expanded
            #logger.debug("Setting expanded = {} for {}".format(expanded, item))
            
            
    def expand(self, index):
        """ Expands the model item specified by the index.
            Overridden from QTreeView to make it persistent (between inspector changes).
        """
        self.setExpanded(index, True)
            
            
    def collapse(self, index):
        """ Expands the model item specified by the index.
            Overridden from QTreeView to make it persistent (between inspector changes).
        """
        self.setExpanded(index, False)

        
    def __obsolete__readModelSettings(self, key, settings):
        """ Reads the persistent program settings.
        
            Will reset the model and thus collapse all nodes.
            
            :param key: key where the setting will be read from
            :param settings: optional QSettings object which can have a group already opened.
            :returns: True if the header state was restored, otherwise returns False
        """ 
        if settings is None:
            settings = QtCore.QSettings()     
            
        valuesJson = settings.value(key, None)
        
        if valuesJson:
            values = ctiLoads(valuesJson)
            self.beginResetModel()
            self.invisibleRootItem.setValuesFromDict(values)
            self.endResetModel()
        else:
            logger.warn("No settings found at: {}".format(key))
    

    def __obsolete__saveProfile(self, key, settings=None):
        """ Writes the view settings to the persistent store
            :param key: key where the setting will be read from
            :param settings: optional QSettings object which can have a group already opened.        
        """         
        logger.debug("Writing model settings for: {}".format(key))
        if settings is None:
            settings = QtCore.QSettings()
            
        values = self.invisibleRootItem.getNonDefaultsDict()
        values_json = ctiDumps(values)
        settings.setValue(key, values_json)

