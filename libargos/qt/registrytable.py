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

""" Classes for displaying the registry contents in a table
"""

from __future__ import print_function

import logging

from libargos.qt import QtCore, QtGui, Qt
from libargos.qt.registry import ClassRegistry, ClassRegItem
from libargos.qt.togglecolumn import ToggleColumnTableView
from libargos.utils.cls import check_class

logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 


class RegistryTableModel(QtCore.QAbstractTableModel):
    
    SORT_ROLE = Qt.UserRole
    
    def __init__(self, registry, attrNames = ('identifier', ), parent=None):
        """ Constructor.
        
            :param registry: Underlying registry. Must descent from ClassRegistry
            :param attrNames: List of attributes that will be displayed (def. only the identifier).
            :param parent: Parent widget
        """
        super(RegistryTableModel, self).__init__(parent)
        check_class(registry, ClassRegistry)
        self.registry = registry
        self.attrNames = attrNames


    def rowCount(self, _parent):
        """ Returns the number of items in the registry."""
        return len(self.registry.items)


    def columnCount(self, _parent):
        """ Returns the number of columns of the registry."""
        return len(self.attrNames)
    

    def data(self, index, role):
        """ Returns the data stored under the given role for the item referred to by the index.
        """    
        if not index.isValid():
            return None
        
        if role != QtCore.Qt.DisplayRole and role != self.SORT_ROLE:
            return None
        
        row = index.row()
        col = index.column()
        item = self.registry.items[row]
        attrName = self.attrNames[col]
        
        if role == QtCore.Qt.DisplayRole:
            return str(getattr(item, attrName))
        
        elif role == self.SORT_ROLE:
            # Use the identifier column as a tie-breaker
            return (getattr(item, attrName), item.identifier) 
        else:
            raise ValueError("Invalid role: {}".format(role))           
        

    def headerData(self, section, orientation, role):
        """ Returns the header for a section (row or column depending on orientation).
            Reimplemented from QAbstractTableModel to make the headers start at 0.
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.attrNames[section]
            else:
                return str(section)
        else:
            return None


    def getRowIndexForItem(self, regItem):
        """ Gets the index (with column=0) for the row that contains the regItem
        """
        try:
            row = self.registry.items.index(regItem)
        except ValueError:
            return QtCore.QModelIndex()
        else:
            return self.index(row, 0)
        
    
class RegistryTableProxModel(QtGui.QSortFilterProxyModel):
    """ Proxy model that overrides the sorting.
        Needed to use the StatsTableModel.SORT_ROLE.
    """
    def lessThan(self, leftIndex, rightIndex):
        """ Returns true if the value of the item referred to by the given index left is less than 
            the value of the item referred to by the given index right, otherwise returns false.
        """
        leftData  = self.sourceModel().data(leftIndex,  RegistryTableModel.SORT_ROLE)
        rightData = self.sourceModel().data(rightIndex, RegistryTableModel.SORT_ROLE)
        
        return leftData < rightData
    
    
class RegistryTableView(ToggleColumnTableView):
    """ QTableView that shows the contents of a registry. 
        Uses QSortFilterProxyModel as a wrapper over the model.
        Will wrap a QSortFilterProxyModel over the RegistryTableModel model to enable sorting.
    """
    def __init__(self, model=None, parent=None):
        """ Constructor
        """
        super(RegistryTableView, self).__init__(parent)
        
        if model is not None:
            self.setModel(model)
            
        #self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        #self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().hide()        
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setWordWrap(True)

        tableHeader = self.horizontalHeader()
        tableHeader.setDefaultAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        tableHeader.setResizeMode(QtGui.QHeaderView.Interactive) # don't set to stretch
        tableHeader.setStretchLastSection(True)


    def setModel(self, model):
        """ Wraps a QSortFilterProxyModel over the RegistryTableModel model to enable sorting.
        """
        # Replacing a current model is not (yet) implemented. We would have to delete the old
        # proxy and selection model (and test this). See the AbstractItemView.setModel docs.
        assert self.model() is None, "Model already defined"
        
        check_class(model, RegistryTableModel)
        proxyTableModel = RegistryTableProxModel(parent=self)
        proxyTableModel.setSourceModel(model)
        proxyTableModel.setSortRole(RegistryTableModel.SORT_ROLE)
        proxyTableModel.setDynamicSortFilter(True) 
        proxyTableModel.setSortCaseSensitivity(Qt.CaseInsensitive)
        
        super(RegistryTableView, self).setModel(proxyTableModel)
        

    def getCurrentRegItem(self): 
        """ Find the current tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        currentSourceIndex = self.model().mapToSource(self.currentIndex())
        registryItems = self.model().sourceModel().registry.items
        return registryItems[currentSourceIndex.row()]

        
    def setCurrentRegItem(self, regItem): 
        """ Find the current tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        check_class(regItem, ClassRegItem, allow_none=True)
        model = self.model().sourceModel()
        sourceRowIndex = model.getRowIndexForItem(regItem)
        rowIndex = self.model().mapFromSource(sourceRowIndex)
        if not rowIndex.isValid():
            logger.warn("Can't select {!r} in table".format(regItem))
        self.setCurrentIndex(rowIndex)
                
