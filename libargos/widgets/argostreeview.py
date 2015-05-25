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

    Currently it supports only selecting one item. That is, the current item is always the 
    selected item. 
    
    The difference between the current item and the selected item(s) is as follows:
    (from: http://doc.qt.digia.com/4.6/model-view-selection.html)
    
    In a view, there is always a current item and a selected item - two independent states. 
    An item can be the current item and selected at the same time. The view is responsible for 
    ensuring that there is always a current item as keyboard navigation, for example, requires 
    a current item.
            
    Current Item:
        There can only be one current item.    
        The current item will be changed with key navigation or mouse button clicks.    
        The current item will be edited if the edit key, F2, is pressed or the item is 
            double-clicked (provided that editing is enabled).    
        The current item is indicated by the focus rectangle.    

    Selected Items:
        There can be multiple selected items.
        The selected state of items is set or unset, depending on several pre-defined modes 
            (e.g., single selection, multiple selection, etc.) when the user interacts with the 
            items.
        The current item can be used together with an anchor to specify a range that should be 
            selected or deselected (or a combination of the two).
        The selected items are indicated with the selection rectangle.
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
    def __init__(self, treeModel=None, parent=None):
        """ Constructor
        """
        super(ArgosTreeView, self).__init__(parent)
        
        if treeModel is not None:
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


    def setCurrentIndex(self, currentIndex):
        """ Sets the current item to be the item at currentIndex.
            Also select the row as to give consistent user feedback.
            See also the notes at the top of this module on current item vs selected item(s). 
        """
        selectionModel = self.selectionModel()
        selectionFlags = (QtGui.QItemSelectionModel.ClearAndSelect | 
                          QtGui.QItemSelectionModel.Rows)
        selectionModel.setCurrentIndex(currentIndex, selectionFlags)  


    def getCurrentIndex(self): 
        """ Returns the index of column 0 of the current item in the underlying model. 
            See also the notes at the top of this module on current item vs selected item(s).        
        """
        selectionModel = self.selectionModel()
        curIndex = selectionModel.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        return col0Index


    def getCurrentItem(self): # TODO: rename? getCurrentItemAndIndex? getCurrentTuple? getCurrent?
        """ Find the current tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index.
            See also the notes at the top of this module on current item vs selected item(s).            
        """
        currentIndex = self.getCurrentIndex()
        currentItem = self.model().getItem(currentIndex)
        return currentItem, currentIndex

    
    def expandPath(self, path):
        """ Expand all nodes in a node-path.
            Returns (item, index) tuple of the last node in the path (the leaf node). This can be 
            reused e.g. to select it.
        """
        iiPath = self.model().findItemAndIndexPath(path)
        for (item, index) in iiPath[1:]: # skip invisible root
            assert index.isValid(), "Sanity check: invalid index in path for item: {}".format(item)
            self.expand(index)
        
        leaf = iiPath[-1]
        return leaf

