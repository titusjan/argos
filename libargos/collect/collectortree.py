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
from libargos.qt import QtGui, QtCore
from libargos.utils.cls import check_class
from libargos.widgets.argostreeview import ArgosTreeView
from libargos.widgets.constants import (TOP_DOCK_HEIGHT)

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
 
        treeHeader = self.header()
        treeHeader.resizeSection(self.COL_ITEM_PATH, 300)
        treeHeader.resizeSection(self.COL_ITEM_NAME, 100)
        treeHeader.setStretchLastSection(True)
        
        model.setHorizontalHeaderLabels (self.HEADERS)

        enabled = dict((name, False) for name in self.HEADERS)
        checked = dict((name, True) for name in self.HEADERS)
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        
    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(300, TOP_DOCK_HEIGHT)
    
    
    def setCurrentRti(self, rti):
        """ Sets the current repo tree item
        """
        check_class(rti, BaseRti)
        model = self.model()
        model.setData(model.index(0, 0), rti.nodePath)
        model.setData(model.index(0, 1), rti.nodeName)
        
        
        
 
