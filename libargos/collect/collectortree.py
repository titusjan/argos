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
    
        NOTE: this class is not meant to be used directly but is 'private' to the Collector().
        That is, plugins should interact with the Collector class, not the CollectorTree()
    """
    HEADERS = ["item path", "item name"]
    (COL_ITEM_PATH, COL_ITEM_NAME) = range(len(HEADERS))    
    
    
    def __init__(self, parent):
        """ Constructor
        """
        super(CollectorTree, self).__init__(parent=parent)
        
        self._comboLabels = None

        nCols = 4
        model = QtGui.QStandardItemModel(3, nCols)
        self.setModel(model)
        self.setTextElideMode(Qt.ElideMiddle) # ellipsis appear in the middle of the text
 
        treeHeader = self.header()
        treeHeader.setStretchLastSection(False)
        treeHeader.setMovable(False)
        
        treeHeader.resizeSection(0, 300) # For item path
        for col in range(1, nCols):
            treeHeader.resizeSection(col, 150)

        labels = [''] * model.columnCount()
        labels[0] = "VisItem Path"
        model.setHorizontalHeaderLabels(labels)
        
        #enabled = dict((name, False) for name in self.HEADERS)
        #checked = dict((name, True) for name in self.HEADERS)
        #self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})
    
