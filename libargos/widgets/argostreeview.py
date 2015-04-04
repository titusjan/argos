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

""" Common functionality, look and feel for all tree views in Argos.
"""
from __future__ import print_function

import logging
from libargos.qt import Qt, QtGui
from libargos.qt.togglecolumn import ToggleColumnTreeView


logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class ArgosTreeView(ToggleColumnTreeView):
    """ QTreeView that defines common functionality, look and feel for all tree views in Argos.
    """
    def __init__(self, treeModel):
        """ Constructor
        """
        super(ArgosTreeView, self).__init__()
        self.setModel(treeModel)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True) 

        treeHeader = self.header()
        treeHeader.setMovable(True)
        treeHeader.setResizeMode(QtGui.QHeaderView.Interactive) # don't set to stretch
        treeHeader.setStretchLastSection(True)

        self.setContextMenuPolicy(Qt.ActionsContextMenu)


    def _getCurrentIndex(self): # TODO: public?
        """ Returns the index of column 0 of the current item in the underlying model. 
        """
        selectionModel = self.selectionModel()
        #assert selectionModel.hasSelection(), "No selection"        
        curIndex = selectionModel.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        return col0Index


    def _getCurrentItem(self):
        """ Find the current tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index.
        """
        currentIndex = self._getCurrentIndex()
        currentItem = self.model().getItem(currentIndex)
        return currentItem, currentIndex

