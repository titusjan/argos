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
from libargos.qt import QtCore, QtGui, QtSlot
from libargos.widgets.argostreeview import ArgosTreeView
from libargos.widgets.constants import RIGHT_DOCK_WIDTH
from libargos.config.configitemdelegate import ConfigItemDelegate
from libargos.config.configtreemodel import ConfigTreeModel

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901


class ConfigTreeView(ArgosTreeView):
    """ Tree widget for manipulating a tree of configuration options.
    """
    def __init__(self, configTreeModel, parent=None):
        """ Constructor
        """
        super(ConfigTreeView, self).__init__(treeModel=configTreeModel, parent=parent)

        configTreeModel.update.connect(self.update)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        
        treeHeader = self.header()
        treeHeader.resizeSection(ConfigTreeModel.COL_VALUE, RIGHT_DOCK_WIDTH / 2)

        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[ConfigTreeModel.COL_NODE_NAME]] = False # Name cannot be unchecked
        enabled[headerNames[ConfigTreeModel.COL_VALUE]] = False # Value cannot be unchecked
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[ConfigTreeModel.COL_NODE_NAME]] = True # Checked by default
        checked[headerNames[ConfigTreeModel.COL_VALUE]] = True # Checked by default
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        self.setItemDelegate(ConfigItemDelegate())
        self.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers) 

        #self.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked |
        #                     QtGui.QAbstractItemView.EditKeyPressed | 
        #                     QtGui.QAbstractItemView.AnyKeyPressed | 
        #                     QtGui.QAbstractItemView.SelectedClicked)
        
        
    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(RIGHT_DOCK_WIDTH, 500)
        
    
    @QtSlot(QtGui.QWidget, QtGui.QAbstractItemDelegate)
    def closeEditor(self, editor, hint):
        """ Finalizes, closes and releases the given editor. 
        """
        # It would be nicer if this method was part of ConfigItemDelegate since createEditor also
        # lives there. However, QAbstractItemView.closeEditor is sometimes called directly,
        # without the QAbstractItemDelegate.closeEditor signal begin emitted, e.g when the 
        # currentItem changes. Therefore we cannot connect to the QAbstractItemDelegate.closeEditor
        # signal to a slot in the ConfigItemDelegate.

        configItemDelegate = self.itemDelegate()
        configItemDelegate.finalizeEditor(editor)
        super(ConfigTreeView, self).closeEditor(editor, hint)

        