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

from argos.qt import QtCore, QtGui, QtWidgets, Qt
from argos.qt.registry import ClassRegistry, ClassRegItem
from argos.qt.togglecolumn import ToggleColumnTableView
from argos.utils.cls import check_class

logger = logging.getLogger(__name__)

QCOLOR_REGULAR = QtGui.QColor('black')
QCOLOR_NOT_IMPORTED = QtGui.QColor('brown')
QCOLOR_ERROR = QtGui.QColor('red')

# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class RegistryTableModel(QtCore.QAbstractTableModel):

    SORT_ROLE = Qt.UserRole

    def __init__(self, registry, attrNames = ('fullName', ), parent=None):
        """ Constructor.

            :param registry: Underlying registry. Must descent from ClassRegistry
            :param attrNames: List of attributes that will be displayed (def. only the fullName).
            :param parent: Parent widget
        """
        super(RegistryTableModel, self).__init__(parent)
        check_class(registry, ClassRegistry)
        self.registry = registry
        self.attrNames = attrNames

        self.regularBrush = QtGui.QBrush(QCOLOR_REGULAR)
        self.notImportedBrush = QtGui.QBrush(QCOLOR_NOT_IMPORTED)
        self.errorBrush = QtGui.QBrush(QCOLOR_ERROR)


    def rowCount(self, _parent):
        """ Returns the number of items in the registry."""
        return len(self.registry.items)


    def columnCount(self, _parent):
        """ Returns the number of columns of the registry."""
        return len(self.attrNames)


    def data(self, index, role=Qt.DisplayRole):
        """ Returns the data stored under the given role for the item referred to by the index.
        """
        if not index.isValid():
            return None

        if role not in (Qt.DisplayRole, self.SORT_ROLE,  Qt.ForegroundRole):
            return None

        row = index.row()
        col = index.column()
        item = self.registry.items[row]
        attrName = self.attrNames[col]

        if role == Qt.DisplayRole:
            return str(getattr(item, attrName))

        elif role == self.SORT_ROLE:
            # Use the fullName column as a tie-breaker
            return (getattr(item, attrName), item.fullName)

        elif role == Qt.ForegroundRole:
            if item.successfullyImported is None:
                return self.notImportedBrush
            elif item.successfullyImported:
                return self.regularBrush
            else:
                return self.errorBrush
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


    def itemFromIndex(self, index):
        """ Gets the item given the model index
        """
        return self.registry.items[index.row()]


    def indexFromItem(self, regItem, col=0):
        """ Gets the index (with column=0) for the row that contains the regItem
            If col is negative, it is counted from the end
        """
        if col < 0:
            col = len(self.attrNames) - col
        try:
            row = self.registry.items.index(regItem)
        except ValueError:
            return QtCore.QModelIndex()
        else:
            return self.index(row, col)


    def emitDataChanged(self, regItem):
        """ Emits the dataChagned signal for the regItem
        """
        leftIndex = self.indexFromItem(regItem, col=0)
        rightIndex = self.indexFromItem(regItem, col=-1)

        logger.debug("Data changed: {} ...{}".format(self.data(leftIndex), self.data(rightIndex)))
        self.dataChanged.emit(leftIndex, rightIndex)



class RegistryTableProxyModel(QtCore.QSortFilterProxyModel):
    """ Proxy model that overrides the sorting and can filter out regItems that are not imported.
    """
    def __init__(self, onlyShowImported=False, parent=None):
        """ Constructor.
            :param onlyShowImported: If true, only regItems that were successfully imported are
                displayed. Default is False.
            :param parent: parent widget
        """
        super(RegistryTableProxyModel, self).__init__(parent=parent)
        self.onlyShowImported = onlyShowImported
        self.setSortRole(RegistryTableModel.SORT_ROLE)
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)


    def filterAcceptsRow(self, sourceRow, sourceParent):
        """ If onlyShowImported is True, regItems that were not (successfully) imported are
            filtered out.
        """
        if not self.onlyShowImported:
            return True

        item = self.sourceModel().registry.items[sourceRow]
        return bool(item.successfullyImported)


    def lessThan(self, leftIndex, rightIndex):
        """ Returns true if the value of the item referred to by the given index left is less than
            the value of the item referred to by the given index right, otherwise returns false.
        """
        leftData  = self.sourceModel().data(leftIndex,  RegistryTableModel.SORT_ROLE)
        rightData = self.sourceModel().data(rightIndex, RegistryTableModel.SORT_ROLE)

        return leftData < rightData


    def itemFromIndex(self, index):
        """ Gets the item given the model index
        """
        sourceIndex = self.mapToSource(index)
        return self.sourceModel().itemFromIndex(sourceIndex)


    def indexFromItem(self, regItem, col=0):
        """ Gets the index (with column=0) for the row that contains the regItem
            If col is negative, it is counted from the end
        """
        sourceIndex = self.sourceModel().indexFromItem(regItem, col=col)
        return self.mapFromSource(sourceIndex)


    def emitDataChanged(self, regItem):
        """ Emits the dataChagned signal for the regItem
        """
        #self.sourceModel().emitDataChanged(regItem) # Does this work?
        leftIndex = self.indexFromItem(regItem, col=0)
        rightIndex = self.indexFromItem(regItem, col=-1)
        self.dataChanged.emit(leftIndex, rightIndex)



class RegistryTableView(ToggleColumnTableView):
    """ QTableView that shows the contents of a registry.
        Uses QSortFilterProxyModel as a wrapper over the model.
        Will wrap a QSortFilterProxyModel over the RegistryTableModel model to enable sorting.
    """
    def __init__(self, model=None, onlyShowImported=False, parent=None):
        """ Constructor

            :param model: a RegistryTableModel that maps the regItems
            :param onlyShowImported: If True, regItems that are not (successfully) imported are
                filtered from the table.
            :param parent: the parent widget
        """
        super(RegistryTableView, self).__init__(parent)

        self._onlyShowImported = onlyShowImported
        if model is not None:

            check_class(model, (RegistryTableModel, RegistryTableProxyModel))
            self.setModel(model)
        else:
            assert False, "not yet implemented"

        #self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        #self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().hide()
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.setTabKeyNavigation(False)

        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setWordWrap(True)

        tableHeader = self.horizontalHeader()
        tableHeader.setDefaultAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        tableHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch
        tableHeader.setStretchLastSection(True)


    @property
    def onlyShowImported(self):
        "If True, regItems that are not (successfully) imported are filtered from the table"
        return self._onlyShowImported


    def getCurrentRegItem(self):
        """ Find the current tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        return self.model().itemFromIndex(self.currentIndex())


    def setCurrentRegItem(self, regItem):
        """ Sets the current registry item.
        """
        rowIndex = self.model().indexFromItem(regItem)
        if not rowIndex.isValid():
            logger.warn("Can't select {!r} in table".format(regItem))
        self.setCurrentIndex(rowIndex)

