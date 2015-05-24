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

""" Collector Tree. 
"""
from __future__ import print_function

import logging

from libargos.repo.baserti import BaseRti
from libargos.qt import Qt, QtGui, QtSlot
from libargos.qt.labeledwidget import LabeledWidget
from libargos.widgets.argostreeview import ArgosTreeView

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class CollectorTree(ArgosTreeView): 
    """ Tree widget for collecting the selected data. Includes an internal tree model.
    """
    HEADERS = ["item path", "item name"]
    (COL_ITEM_PATH, COL_ITEM_NAME) = range(len(HEADERS))    
    
    def __init__(self):
        """ Constructor
        """
        super(CollectorTree, self).__init__()
        
        model = QtGui.QStandardItemModel(3, len(self.HEADERS))
        self.setModel(model)
        self.setTextElideMode(Qt.ElideMiddle) # ellipsis appear in the middle of the text
 
        treeHeader = self.header()
        treeHeader.resizeSection(self.COL_ITEM_PATH, 300)
        treeHeader.resizeSection(self.COL_ITEM_NAME, 100)
        treeHeader.setStretchLastSection(True)
        
        model.setHorizontalHeaderLabels (self.HEADERS)

        enabled = dict((name, False) for name in self.HEADERS)
        checked = dict((name, True) for name in self.HEADERS)
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})
        

    @QtSlot(BaseRti)
    def updateFromRti(self, rti):
        """ Updates the current VisItem from the contents of the repo tree item.
        
            Is a slot but the signal is usually connected to the Collector, which then call
            this function directly.
        """
        assert rti.asArray is not None, "rti must have array"
        model = self.model()
        
        pathItem = QtGui.QStandardItem(rti.nodePath)
        pathItem.setEditable(False)
        model.setItem(0, 0, pathItem)

        lineEdit = QtGui.QLineEdit(rti.nodeName)
        editor = LabeledWidget(QtGui.QLabel("edit"), lineEdit, layoutSpacing=0)
        self.setIndexWidget(model.index(0, 1), editor) 
        
        
