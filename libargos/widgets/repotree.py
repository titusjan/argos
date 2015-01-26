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
from libargos.qt import QtGui, QtCore, QtSlot
from libargos.qt.togglecolumn import ToggleColumnTreeView

from libargos.repo.repository import RepositoryTreeModel
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
        treeHeader.resizeSection(RepositoryTreeModel.COL_NODE_NAME, 300)
        treeHeader.resizeSection(RepositoryTreeModel.COL_FILE_NAME, 500)
        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[0]] = False # Fist column cannot be unchecked
        self.addHeaderContextMenu(enabled=enabled, checkable={})

        
    def loadRepoTreeItem(self, repoTreeItem, expand=False, 
                         position=None, parentIndex=QtCore.QModelIndex()):
        """ Loads a tree item in the repository and expands it.
            If position is None the child will be appended as the last child of the parent.
            Returns the index of the newly inserted RTI.
        """
        assert repoTreeItem.parentItem is None, "repoTreeItem {!r}".format(repoTreeItem)
        storeRootIndex = self.model().insertItem(repoTreeItem, position=position, 
                                                 parentIndex=parentIndex)
        self.setExpanded(storeRootIndex, expand)
        return storeRootIndex


    def loadFile(self, fileName, expand=False, rtiClass=None):
        """ Loads a file in the repository. Autodetects the RTI type if needed.
            Returns the index of the newly inserted RTI
        """
        if rtiClass is None:
            rtiClass = detectRtiFromFileName(fileName)
        repoTreeItem = rtiClass.createFromFileName(fileName)
        return self.loadRepoTreeItem(repoTreeItem, expand=expand)
    
    
    def selectByIndex(self, selectionIndex):
        """ Selects the node with index selection index
        """
        selectionModel = self.selectionModel()
        selectionModel.setCurrentIndex(selectionIndex, QtGui.QItemSelectionModel.ClearAndSelect)    
        logger.debug("selected tree item: has selection: {}".format(selectionModel.hasSelection()))


    def _getSelectedIndex(self): # TODO: public?
        """ Returns the index of the selected item in the repository. 
        """
        selectionModel = self.selectionModel()
        assert selectionModel.hasSelection(), "No selection"        
        curIndex = selectionModel.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        return col0Index


    def _getSelectedItem(self):
        """ Find the selected root tree item (and the selected index while we're at it)
            Returns a tuple with the selected item, and its index.
        """
        selectedIndex = self._getSelectedIndex()
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

        
    @QtSlot()
    def removeSelectedFile(self):
        """ Finds the root of of the selected item, which represents a file, 
            and removes it from the list.
        """
        logger.debug("removeSelectedFile")
        selectedIndex = self._getSelectedIndex()
        topLevelIndex = self.model().findTopLevelItemIndex(selectedIndex)
        self.model().deleteItemByIndex(topLevelIndex) # this will close the items resources.
        
        
    @QtSlot()
    def reloadFileOfSelectedItem(self):
        """ Finds the repo tree item that holds the file of the item that was selected, 
            and reloads.
            Reloading is done by removing the repo tree item and inserting a new one.
        """
        logger.debug("reloadFileOfSelectedItem")
        selectedIndex = self._getSelectedIndex()
        fileRtiIndex = self.model().findFileRtiIndex(selectedIndex)
        fileRtiParentIndex = fileRtiIndex.parent()
        fileRti = self.model().getItem(fileRtiIndex)
        fileName = fileRti.fileName
        rtiClass = type(fileRti)
        position = fileRti.childNumber()
        
        # Delete old RTI
        self.model().deleteItemByIndex(fileRtiIndex) # this will close the items resources.
        
        # Insert a new one instead.
        newRti = rtiClass.createFromFileName(fileName)
        newRtiIndex = self.loadRepoTreeItem(newRti, expand=True, position=position,  
                                            parentIndex=fileRtiParentIndex)
        self.selectByIndex(newRtiIndex)
        return newRtiIndex
     
