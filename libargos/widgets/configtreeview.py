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

""" Configuration tree. Can be used to manipulate the configuration of an inspector.

"""
from __future__ import print_function

import logging
from libargos.qt import QtCore, QtGui, QtSlot
from libargos.widgets.argostreeview import ArgosTreeView
from libargos.widgets.constants import RIGHT_DOCK_WIDTH
from libargos.config.configtreemodel import ConfigTreeModel

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901


class ConfigItemDelegate(QtGui.QStyledItemDelegate):
    """ Provides editing facilities for config tree items.
        Creates an editor based on the underlying config tree item at an index.
        
        We don't use a QItemEditorFactory since that is typically registered for a type of 
        QVariant. We then would have to make a new UserType QVariant for (each?) CTIs.
        This is cumbersome and possibly unPyQTtonic :-)
    """
    def paint(self, painter, option, index):

        painted = False
                
        if index.column() == ConfigTreeModel.COL_VALUE:

            # We take the value via the model to be consistent with setModelData
            value = index.model().data(index, QtCore.Qt.EditRole) 
            cti = index.model().getItem(index)
            painted = cti.paintDisplayValue(painter, option, value)
        
        if not painted:
            super(ConfigItemDelegate, self).paint(painter, option, index)
        
    
    def createEditor(self, parent, option, index):
        """ Returns the widget used to change data from the model and can be reimplemented to 
            customize editing behavior.
        """
        assert index.isValid(), "sanity check failed: invalid index"
        
        cti = index.model().getItem(index)
        editor = cti.createEditor(self, parent, option)
        return editor
    

    def setEditorData(self, editor, index):
        """ Provides the widget with data to manipulate.
            Calls the setEditorValue of the config tree item at the index. 
        
            :type editor: QWidget
            :type index: QModelIndex
        """
        # We take the value via the model to be consistent with setModelData
        value = index.model().data(index, QtCore.Qt.EditRole)
        cti = index.model().getItem(index)
        cti.setEditorValue(editor, value)
        

    def setModelData(self, editor, model, index):
        """ Gets data from the editor widget and stores it in the specified model at the item index.
            Does this by caling setModelData of the config tree item at the index.
            
            :type editor: QWidget
            :type model: ConfigTreeModel
            :type index: QModelIndex
        """
        cti = model.getItem(index)
        value = cti.getEditorValue(editor)
        
        # The value is set via the model so that signals are emitted
        model.setData(index, value, QtCore.Qt.EditRole)


    def updateEditorGeometry(self, editor, option, index):
        """ Ensures that the editor is displayed correctly with respect to the item view.
        """
        editor.setGeometry(option.rect)
        
    @QtSlot()
    def commitAndCloseEditor(self, *args, **kwargs):
        """ Calls the signals to commit the data and close the editor
        """
        #logger.debug("commitAndCloseEditor: {} {}".format(args, kwargs))
        editor = self.sender() # TODO somehow make parameter?
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QtGui.QAbstractItemDelegate.NoHint)        



class ConfigTreeView(ArgosTreeView):
    """ Tree widget for manipulating a tree of configuration options.
    """
    def __init__(self, configTreeModel):
        """ Constructor
        """
        super(ConfigTreeView, self).__init__(configTreeModel)

        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        
        treeHeader = self.header()
        treeHeader.resizeSection(ConfigTreeModel.COL_NODE_NAME, RIGHT_DOCK_WIDTH / 2)
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
        
