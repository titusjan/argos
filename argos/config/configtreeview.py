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

""" Configuration tree. Can be used to manipulate the a ConfigurationModel.

"""
from __future__ import print_function

import logging
from argos.qt import QtCore, QtWidgets, QtSlot
from argos.widgets.argostreeview import ArgosTreeView
from argos.widgets.constants import RIGHT_DOCK_WIDTH, DOCK_SPACING, DOCK_MARGIN
from argos.config.configitemdelegate import ConfigItemDelegate
from argos.config.configtreemodel import ConfigTreeModel

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901


class ConfigWidget(QtWidgets.QWidget):
    """ Shows the configuration. At the moment only the confg tree view.
    """
    def __init__(self, configTreeModel, parent=None):
        """ Constructor.
            :param parent:
        """
        super(ConfigWidget, self).__init__(parent=parent)
        self.configTreeView = ConfigTreeView(configTreeModel, parent=self)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(self.configTreeView)
        self.mainLayout.setSpacing(DOCK_SPACING)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)


class ConfigTreeView(ArgosTreeView):
    """ Tree widget for manipulating a tree of configuration options.
    """
    def __init__(self, configTreeModel, parent=None):
        """ Constructor
        """
        super(ConfigTreeView, self).__init__(treeModel=configTreeModel, parent=parent)

        self.expanded.connect(configTreeModel.expand)
        self.collapsed.connect(configTreeModel.collapse)
        #configTreeModel.update.connect(self.update) # not necessary
        #self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)

        treeHeader = self.header()
        treeHeader.resizeSection(ConfigTreeModel.COL_NODE_NAME, RIGHT_DOCK_WIDTH * 0.5)
        treeHeader.resizeSection(ConfigTreeModel.COL_VALUE, RIGHT_DOCK_WIDTH * 0.5)

        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[ConfigTreeModel.COL_NODE_NAME]] = False # Name cannot be unchecked
        enabled[headerNames[ConfigTreeModel.COL_VALUE]] = False # Value cannot be unchecked
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[ConfigTreeModel.COL_NODE_NAME]] = True # Checked by default
        checked[headerNames[ConfigTreeModel.COL_VALUE]] = True # Checked by default
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)
        self.setItemDelegate(ConfigItemDelegate())
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

        #self.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked |
        #                     QtWidgets.QAbstractItemView.EditKeyPressed |
        #                     QtWidgets.QAbstractItemView.AnyKeyPressed |
        #                     QtWidgets.QAbstractItemView.SelectedClicked)


    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(RIGHT_DOCK_WIDTH, 500)


    @QtSlot(QtWidgets.QWidget, QtWidgets.QAbstractItemDelegate.EndEditHint)
    def closeEditor(self, editor, hint):
        """ Finalizes, closes and releases the given editor.
        """
        # It would be nicer if this method was part of ConfigItemDelegate since createEditor also
        # lives there. However, QAbstractItemView.closeEditor is sometimes called directly,
        # without the QAbstractItemDelegate.closeEditor signal begin emitted, e.g when the
        # currentItem changes. Therefore we cannot connect the QAbstractItemDelegate.closeEditor
        # signal to a slot in the ConfigItemDelegate.
        configItemDelegate = self.itemDelegate()
        configItemDelegate.finalizeEditor(editor)

        super(ConfigTreeView, self).closeEditor(editor, hint)


    def expandBranch(self, index=None, expanded=None):
        """ Expands or collapses the node at the index and all it's descendants.
            If expanded is True the nodes will be expanded, if False they will be collapsed, and if
            expanded is None the expanded attribute of each item is used.
            If parentIndex is None, the invisible root will be used (i.e. the complete forest will
            be expanded).
        """
        configModel = self.model()
        if index is None:
            #index = configTreeModel.createIndex()
            index = QtCore.QModelIndex()

        if index.isValid():
            if expanded is None:
                item = configModel.getItem(index)
                self.setExpanded(index, item.expanded)
            else:
                self.setExpanded(index, expanded)

        for rowNr in range(configModel.rowCount(index)):
            childIndex = configModel.index(rowNr, configModel.COL_NODE_NAME, parentIndex=index)
            self.expandBranch(index=childIndex, expanded=expanded)

