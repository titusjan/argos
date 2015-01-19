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

""" Repository tree.
"""
from __future__ import print_function

import logging
from libargos.qt import QtGui, QtSlot
from libargos.qt.togglecolumn import ToggleColumnTreeView

from libargos.repo.filesytemrti import detectRtiFromFileName


logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class RepoTreeView(ToggleColumnTreeView):
    """ Tree widget for browsing the data repository.
    """
    def __init__(self, repoTreeModel):
        """ Constructor
        """
        super(RepoTreeView, self).__init__()
        self.setModel(repoTreeModel)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems) # TODO: SelectRows
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True) 

        treeHeader = self.header()
        treeHeader.setMovable(True)
        treeHeader.setStretchLastSection(False)  
        treeHeader.resizeSection(0, 300)
        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[0]] = False # Fist column cannot be unchecked
        self.addHeaderContextMenu(enabled=enabled, checkable={})

        
    def loadRepoTreeItem(self, repoTreeItem, expand=False):
        """ Loads a tree item in the repository and expands it.
        """
        assert repoTreeItem.parentItem is None, "repoTreeItem {!r}".format(repoTreeItem)
        storeRootIndex = self.model().insertItem(repoTreeItem)
        self.setExpanded(storeRootIndex, expand)


    def loadFile(self, fileName, expand=False, rtiClass=None):
        """ Loads a file in the repository. Autodetects the RTI type if needed.
        """
        if rtiClass is None:
            rtiClass = detectRtiFromFileName(fileName)
        repoTreeItem = rtiClass.createFromFileName(fileName)
        self.loadRepoTreeItem(repoTreeItem, expand=expand)
        
        
    def _getSelectedItemIndex(self):
        """ Returns the index of the selected item in the repository. 
        """
        selectionModel = self.selectionModel()
        assert selectionModel.hasSelection(), "No selection"        
        curIndex = selectionModel.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        return col0Index


    def _getSelectedItem(self):
        """ Returns a tuple with the selected item, and its index, in the repository. 
        """
        selectedIndex = self._getSelectedItemIndex()
        selectedItem = self.model().getItem(selectedIndex)
        return selectedItem, selectedIndex

    
    @QtSlot()
    def openSelectedItem(self):
        """ Opens the selected item in the repository.
        """
        logger.debug("openSelectedItem")
        selectedItem, selectedIndex = self._getSelectedItem()
        selectedItem.open()
        self.expand(selectedIndex) # to visit the children and thus show the 'open' icons
    
         
    @QtSlot()
    def closeSelectedItem(self):
        """ Closes the selected item in the repository. 
            All its children will be unfetched and closed.
        """
        logger.debug("closeSelectedItem")
        selectedItem, selectedIndex = self._getSelectedItem()
        
        # First we remove all the children, this will close them as well.
        self.model().removeAllChildrenAtIndex(selectedIndex)
        selectedItem.close()
        self.collapse(selectedIndex) # otherwise the children will be fetched immediately
        

