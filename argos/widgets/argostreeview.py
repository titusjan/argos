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
from argos.qt import QtCore, QtWidgets
from argos.qt.togglecolumn import ToggleColumnTreeView
from argos.qt.treemodels import BaseTreeModel
from argos.utils.cls import check_class
from argos.widgets.constants import TREE_ICON_SIZE


logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class ArgosTreeView(ToggleColumnTreeView):
    """ QTreeView that defines common functionality, look and feel for all tree views in Argos.

        The model must be a BaseTreeModel
    """
    def __init__(self, treeModel=None, parent=None):
        """ Constructor
        """
        super(ArgosTreeView, self).__init__(parent)

        if treeModel is not None:
            self.setModel(treeModel)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True)
        self.setIconSize(TREE_ICON_SIZE)

        treeHeader = self.header()
        treeHeader.setSectionsMovable(True)
        treeHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch
        treeHeader.setStretchLastSection(True)


    def setModel(self, model):
        """ Sets the model.
            Checks that the model is a
        """
        check_class(model, BaseTreeModel)
        super(ArgosTreeView, self).setModel(model)


    def setCurrentIndex(self, currentIndex):
        """ Sets the current item to be the item at currentIndex.
            Also select the row as to give consistent user feedback.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        selectionModel = self.selectionModel()
        selectionFlags = (QtCore.QItemSelectionModel.ClearAndSelect |
                          QtCore.QItemSelectionModel.Rows)
        selectionModel.setCurrentIndex(currentIndex, selectionFlags)


    def getRowCurrentIndex(self):
        """ Returns the index of column 0 of the current item in the underlying model.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        curIndex = self.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        return col0Index


    def getCurrentItem(self): # TODO: rename? getCurrentItemAndIndex? getCurrentTuple? getCurrent?
        """ Find the current tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index. The item may be None.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        currentIndex = self.getRowCurrentIndex()
        currentItem = self.model().getItem(currentIndex)
        return currentItem, currentIndex


    def expandPath(self, path):
        """ Follows the path and expand all nodes along the way.
            Returns (item, index) tuple of the last node in the path (the leaf node). This can be
            reused e.g. to select it.
        """
        iiPath = self.model().findItemAndIndexPath(path)
        for (item, index) in iiPath[1:]: # skip invisible root
            assert index.isValid(), "Sanity check: invalid index in path for item: {}".format(item)
            self.expand(index)

        leaf = iiPath[-1]
        return leaf


    def expandBranch(self, index=None, expanded=True):
        """ Expands or collapses the node at the index and all it's descendants.

            If expanded is True the nodes will be expanded, if False they will be collapsed.

            If parentIndex is None, the invisible root will be used (i.e. the complete forest will
            be expanded).
        """
        treeModel = self.model()
        if index is None:
            index = QtCore.QModelIndex()

        if index.isValid():
            self.setExpanded(index, expanded)

        for rowNr in range(treeModel.rowCount(index)):
            childIndex = treeModel.index(rowNr, 0, parentIndex=index)
            self.expandBranch(index=childIndex, expanded=expanded)

